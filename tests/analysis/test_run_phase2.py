import pytest
import pandas as pd
import numpy as np
from src.analysis.run_phase2 import _is_kde_safe

def test_is_kde_safe_constant_feature():
    """Test 1 - Constant Feature"""
    df = pd.DataFrame({"feat": [5, 5, 5, 5, 5]})
    assert _is_kde_safe(df, "feat") is False

def test_is_kde_safe_single_unique_value():
    """Test 2 - Single Unique Value"""
    df = pd.DataFrame({"feat": [10, 10, 10]})
    assert _is_kde_safe(df, "feat") is False

def test_is_kde_safe_near_zero_variance():
    """Test 3 - Near-Zero Variance"""
    df = pd.DataFrame({"feat": [1.00000001, 1.00000001, 1.00000001]})
    assert _is_kde_safe(df, "feat") is False

def test_is_kde_safe_nan_heavy():
    """Test 4 - NaN-Heavy Data"""
    df = pd.DataFrame({"feat": [np.nan, np.nan, 5, np.nan]})
    assert _is_kde_safe(df, "feat") is False

def test_is_kde_safe_insufficient_data():
    """Test 5 - Insufficient Data"""
    df = pd.DataFrame({"feat": [5]})
    assert _is_kde_safe(df, "feat") is False

def test_is_kde_safe_normal_continuous():
    """Test 6 - Normal Continuous Data"""
    df = pd.DataFrame({"feat": [1, 2, 3, 4, 5]})
    assert _is_kde_safe(df, "feat") is True

def test_is_kde_safe_mixed_hue_groups():
    """Test 7 - Mixed Hue Groups"""
    df = pd.DataFrame({
        "feat": [1, 2, 3, 5, 5, 5],
        "group": ["A", "A", "A", "B", "B", "B"]
    })
    # Group A is valid, but Group B is constant. 
    # Therefore, KDE is unsafe for the entire plot.
    assert _is_kde_safe(df, "feat", "group") is False
