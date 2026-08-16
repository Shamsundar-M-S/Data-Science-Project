import pytest
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from src.analysis.plot_style import get_compound_palette
from src.analysis.run_phase4 import _plot_tyre_degradation

def test_get_compound_palette_resolves_all_colors():
    compounds = ['ULTRASOFT', 'SUPERSOFT', 'SOFT', 'MEDIUM', 'HARD', 'FUTURE_COMPOUND_X']
    palette = get_compound_palette(compounds)
    
    # Check that all compounds are in the palette
    for compound in compounds:
        assert compound in palette
        assert isinstance(palette[compound], str)
        assert palette[compound].startswith('#')

    # Check canonical colors for known compounds
    assert palette['SOFT'] == '#ef4444'
    assert palette['MEDIUM'] == '#eab308'
    assert palette['HARD'] == '#ffffff'

    # Check historical canonical colors
    assert palette['ULTRASOFT'] == '#b24c96'
    assert palette['SUPERSOFT'] == '#da291c'

    # Check deterministic fallback for unknown
    assert 'FUTURE_COMPOUND_X' in palette
    assert palette['FUTURE_COMPOUND_X'].startswith('#')

def test_mixed_category_plot_success(tmp_path):
    # Mock dataframe with known, historical, and unknown compounds
    df = pd.DataFrame({
        'tyre_life_start': [1, 5, 10, 15, 20, 25],
        'degradation_s_per_lap': [0.05, 0.06, 0.04, 0.07, 0.03, 0.08],
        'Compound': ['SOFT', 'MEDIUM', 'ULTRASOFT', 'SUPERSOFT', 'UNKNOWN_X', 'UNKNOWN_Y']
    })
    
    # We will simulate the same logic as _plot_tyre_degradation directly 
    # to ensure palette dictionary provides keys correctly for Seaborn.
    palette = get_compound_palette(df['Compound'].unique())
    
    fig = plt.figure(figsize=(10, 6))
    
    try:
        sns.scatterplot(data=df, x='tyre_life_start', y='degradation_s_per_lap', hue='Compound', palette=palette, s=100)
    except ValueError as e:
        pytest.fail(f"Plotting failed with ValueError: {e}")
    finally:
        plt.close(fig)
