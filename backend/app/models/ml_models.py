"""
ML Model loading and prediction logic
"""
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ModelCache:
    """
    Singleton class to load models once at startup and cache in memory
    Avoids reloading models on every prediction request
    """

    _instance = None
    _models = {}
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_models(self, models_dir: Path):
        """
        Load all models at startup

        Args:
            models_dir: Directory containing .pkl model files

        Raises:
            FileNotFoundError: If model files don't exist
            Exception: If model loading fails
        """
        if self._initialized:
            logger.info("Models already loaded, skipping...")
            return

        logger.info(f"Loading models from {models_dir}")

        try:
            # Load grade distribution model (primary model)
            grade_dist_path = models_dir / 'model_grade_distribution.pkl'
            if not grade_dist_path.exists():
                raise FileNotFoundError(f"Model not found: {grade_dist_path}")

            self._models['grade_distribution'] = joblib.load(grade_dist_path)
            logger.info("Loaded grade_distribution model")

            # Load full features model (secondary model)
            full_path = models_dir / 'model_full.pkl'
            if not full_path.exists():
                raise FileNotFoundError(f"Model not found: {full_path}")

            self._models['full'] = joblib.load(full_path)
            logger.info("Loaded full features model")

            # Load model metadata (performance metrics)
            self._load_model_metadata(models_dir)

            self._initialized = True
            logger.info(f"Successfully loaded {len(self._models)} models")

        except Exception as e:
            logger.error(f"Failed to load models: {str(e)}")
            raise

    def _load_model_metadata(self, models_dir: Path):
        """Load model performance metrics from comparison CSV"""
        import pandas as pd

        comparison_path = models_dir / 'model_comparison.csv'
        if comparison_path.exists():
            df = pd.read_csv(comparison_path)

            # Store metadata for each model
            for model_type in ['grade_distribution', 'full']:
                # Find matching row in comparison CSV
                model_name_map = {
                    'grade_distribution': 'Ridge Regression (Grade Distribution)',
                    'full': 'Random Forest (All Features)'
                }

                row = df[df['model_name'] == model_name_map[model_type]]
                if not row.empty:
                    self._models[model_type]['metadata'] = {
                        'mae': float(row['mae'].values[0]),
                        'rmse': float(row['rmse'].values[0]),
                        'r2': float(row['r2'].values[0])
                    }
                    logger.info(f"Loaded metadata for {model_type}: MAE={self._models[model_type]['metadata']['mae']:.3f}")

    def predict(
        self,
        model_type: str,
        features: Dict[str, float]
    ) -> Tuple[float, Dict]:
        """
        Run prediction with preprocessing

        Args:
            model_type: "grade_distribution" or "full"
            features: Dictionary of feature values

        Returns:
            tuple: (predicted_gpa, metadata_dict)
                - predicted_gpa: Float GPA value (2.5-4.0 range)
                - metadata_dict: Contains confidence_interval, model_info

        Raises:
            ValueError: If model_type is invalid or features are missing
        """
        if not self._initialized:
            raise RuntimeError("Models not loaded. Call load_models() first.")

        if model_type not in self._models:
            raise ValueError(f"Invalid model_type: {model_type}. Choose 'grade_distribution' or 'full'")

        model_data = self._models[model_type]
        model = model_data['model']
        scaler = model_data['scaler']
        feature_list = model_data['features']

        # Extract feature values in correct order
        try:
            feature_values = [features[f] for f in feature_list]
        except KeyError as e:
            missing_feature = str(e).strip("'")
            raise ValueError(f"Missing required feature: {missing_feature}. Required features: {feature_list}")

        # Check for None values
        if any(v is None for v in feature_values):
            none_features = [feature_list[i] for i, v in enumerate(feature_values) if v is None]
            raise ValueError(f"Features cannot be None: {none_features}")

        # Scale features (StandardScaler normalization)
        feature_array = np.array([feature_values])
        X_scaled = scaler.transform(feature_array)

        # Predict
        y_pred = model.predict(X_scaled)[0]

        # Clip prediction to valid GPA range
        y_pred = np.clip(y_pred, 0.0, 4.0)

        # Calculate confidence interval using MAE
        # CI = predicted_value ± (z_score * MAE)
        # For 95% CI, z_score = 1.96
        mae = model_data.get('metadata', {}).get('mae', 0.1)
        margin = 1.96 * mae
        confidence_interval = {
            'lower': max(0.0, y_pred - margin),
            'upper': min(4.0, y_pred + margin)
        }

        metadata = {
            'confidence_interval': confidence_interval,
            'model_info': self.get_model_info(model_type)
        }

        return float(y_pred), metadata

    def get_model_info(self, model_type: str) -> Dict:
        """
        Return model metadata for API response

        Args:
            model_type: "grade_distribution" or "full"

        Returns:
            dict: Model information including name, features, metrics
        """
        if model_type not in self._models:
            raise ValueError(f"Invalid model_type: {model_type}")

        model_data = self._models[model_type]

        # Model names
        model_names = {
            'grade_distribution': 'Ridge Regression',
            'full': 'Random Forest'
        }

        # Model descriptions
        descriptions = {
            'grade_distribution': 'Predicts GPA using only grade distribution features (works for all courses)',
            'full': 'Predicts GPA using grade distribution + grading structure features (limited to courses with grading data)'
        }

        info = {
            'model_type': model_type,
            'model_name': model_names.get(model_type, 'Unknown'),
            'description': descriptions.get(model_type, ''),
            'features': model_data['features'],
            'num_features': len(model_data['features'])
        }

        # Add metrics if available
        if 'metadata' in model_data:
            info.update({
                'mae': model_data['metadata']['mae'],
                'rmse': model_data['metadata']['rmse'],
                'r2': model_data['metadata']['r2']
            })

        return info

    def get_all_models_info(self) -> list:
        """
        Get information about all loaded models

        Returns:
            list: List of model info dictionaries
        """
        if not self._initialized:
            return []

        return [self.get_model_info(model_type) for model_type in self._models.keys()]

    def is_loaded(self) -> bool:
        """Check if models are loaded"""
        return self._initialized

    def get_model_count(self) -> int:
        """Get number of loaded models"""
        return len(self._models) if self._initialized else 0


# Global model cache instance
model_cache = ModelCache()
