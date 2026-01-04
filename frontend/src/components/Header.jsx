import React from 'react';
import { NavLink } from 'react-router-dom';

const Header = () => {
  return (
    <header className="header">
      <h1>UC Berkeley Course Difficulty Predictor</h1>
      <nav>
        <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
          Predict
        </NavLink>
        <NavLink to="/courses" className={({ isActive }) => isActive ? 'active' : ''}>
          Browse Courses
        </NavLink>
        <NavLink to="/about" className={({ isActive }) => isActive ? 'active' : ''}>
          About
        </NavLink>
      </nav>
    </header>
  );
};

export default Header;
