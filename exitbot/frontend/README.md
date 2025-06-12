# ExitBot HR App - Refactored Architecture

This directory contains the refactored ExitBot HR application, which has been transformed from a monolithic structure into a modular, component-based architecture.

## Architecture Overview

The application follows a modular design with clear separation of concerns:

```
exitbot/frontend/
  ├── components/         # Reusable UI components
  ├── pages/              # Page-level components
  ├── utils/              # Utility functions
  ├── views/              # Feature-specific views
  ├── api_client.py       # API interaction layer
  ├── hr_app.py           # Original monolithic app (legacy)
  └── refactored_hr_app.py # New modular main app
```

### Key Components

- **utils/** - Core utilities:
  - `error_handling.py` - Error display and processing
  - `formatting.py` - Date and number formatting
  - `state_management.py` - Session state management
  - `data_loading.py` - Standardized API data loading

- **pages/** - Primary page components:
  - `dashboard.py` - Main dashboard
  - `interviews.py` - Interview list and details
  - `reports.py` - Reports and data export
  - `settings.py` - User and system settings

- **components/** - Reusable UI elements:
  - `design_system.py` - CSS and visual styles
  - `login.py` - Authentication UI
  - `dashboard_cards.py` - Metrics and charts

## Running the Application

To run the refactored application:

```bash
cd exitbot
streamlit run frontend/refactored_hr_app.py
```

To run the original (legacy) application:

```bash
cd exitbot
streamlit run frontend/hr_app.py
```

## Implementation Details

The refactoring follows these principles:

1. **Separation of Concerns**: UI, data loading, and state management are clearly separated
2. **Component Reuse**: Common UI patterns extracted as reusable components
3. **State Management**: Centralized, consistent state handling
4. **Error Handling**: Standardized error display and reporting
5. **Data Flow**: Clear, unidirectional data flow from API to UI

## Transition Strategy

The refactored app (`refactored_hr_app.py`) runs in parallel with the legacy app (`hr_app.py`), sharing the same API client, allowing for a gradual transition.

## Future Improvements

Potential areas for future enhancements:

- Add more view components for detailed data visualization
- Implement lazy loading for performance optimization
- Add comprehensive error recovery mechanisms
- Implement more advanced caching strategies 