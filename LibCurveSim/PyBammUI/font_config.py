"""
Font Configuration Module for Japanese Text Support

This module configures matplotlib to properly display Japanese text
by setting up appropriate fonts and handling font warnings.
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import warnings
import os
import sys

def setup_japanese_fonts():
    """
    Set up Japanese fonts for matplotlib.
    
    This function attempts to configure matplotlib to use Japanese fonts
    for proper display of Japanese text in plots and graphs.
    """
    
    # Suppress font warnings to reduce console noise
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.font_manager')
    warnings.filterwarnings('ignore', category=UserWarning, message='.*Glyph.*missing from font.*')
    warnings.filterwarnings('ignore', category=UserWarning, message='.*findfont.*')
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.backends')
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.pyplot')
    
    # Suppress specific glyph warnings for Japanese characters
    warnings.filterwarnings('ignore', category=UserWarning, message='.*KATAKANA.*missing from font.*')
    warnings.filterwarnings('ignore', category=UserWarning, message='.*HIRAGANA.*missing from font.*')
    warnings.filterwarnings('ignore', category=UserWarning, message='.*CJK UNIFIED IDEOGRAPH.*missing from font.*')
    warnings.filterwarnings('ignore', category=UserWarning, message='.*PROLONGED SOUND MARK.*missing from font.*')
    
    # Also suppress tkinter font warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='tkinter')
    warnings.filterwarnings('ignore', category=UserWarning, message='.*func.*args.*')
    
    # List of Japanese fonts to try (in order of preference)
    # Note: DejaVu Sans is moved to the end as it doesn't support Japanese characters
    japanese_fonts = [
        'Noto Sans CJK JP',  # Best cross-platform Japanese font
        'Yu Gothic',  # Modern Windows Japanese font
        'Meiryo',  # Windows Japanese font
        'MS Gothic',  # Windows system fonts
        'Hiragino Sans',  # macOS
        'Hiragino Kaku Gothic ProN',  # macOS alternative
        'Arial Unicode MS',  # Windows with Unicode support
        'IPAexGothic',  # IPA fonts
        'IPAPGothic',
        'IPAGothic',
        'Takao Gothic',  # Takao fonts
        'Takao',
        'VL PGothic',  # VL fonts
        'VL Gothic',
        'DejaVu Sans',  # Fallback font (doesn't support Japanese)
    ]
    
    # Try to find an available Japanese font
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    selected_font = None
    
    # First, try to find a Japanese-capable font
    for font in japanese_fonts:
        if font in available_fonts:
            selected_font = font
            break
    
    # If no Japanese font is found, try alternative approaches
    if selected_font is None:
        # Try to find any font that might support CJK characters
        cjk_fonts = []
        for font_obj in fm.fontManager.ttflist:
            font_name = font_obj.name.lower()
            if any(keyword in font_name for keyword in ['cjk', 'japanese', 'jp', 'gothic', 'mincho', 'sans']):
                cjk_fonts.append(font_obj.name)
        
        if cjk_fonts:
            selected_font = cjk_fonts[0]
            print(f"Found potential CJK font: {selected_font}")
        else:
            # Final fallback - use system default but configure for better Unicode support
            selected_font = plt.rcParams['font.sans-serif'][0] if plt.rcParams['font.sans-serif'] else 'DejaVu Sans'
            print("Warning: No Japanese fonts found. Using system default font.")
            print("Japanese text may not display correctly.")
    else:
        print(f"Using font: {selected_font}")
    
    # Configure matplotlib to use the selected font with better fallback
    plt.rcParams['font.family'] = 'sans-serif'
    # Put selected font first, then add other potential Japanese fonts as fallbacks
    fallback_fonts = [selected_font] + [f for f in japanese_fonts if f != selected_font] + plt.rcParams['font.sans-serif']
    plt.rcParams['font.sans-serif'] = fallback_fonts
    
    # Set font size for better readability
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = 10
    plt.rcParams['xtick.labelsize'] = 9
    plt.rcParams['ytick.labelsize'] = 9
    plt.rcParams['legend.fontsize'] = 9
    
    # Enable Unicode support
    plt.rcParams['axes.unicode_minus'] = False
    
    return selected_font

def install_japanese_fonts_guide():
    """
    Print instructions for installing Japanese fonts on different systems.
    """
    print("\n" + "="*60)
    print("Japanese Font Installation Guide")
    print("="*60)
    
    print("\nFor better Japanese text display, install Japanese fonts:")
    
    print("\n🪟 Windows:")
    print("  - Japanese fonts are usually pre-installed")
    print("  - If needed, install 'Noto Sans CJK JP' from Google Fonts")
    
    print("\n🍎 macOS:")
    print("  - Hiragino Sans is pre-installed")
    print("  - Install 'Noto Sans CJK JP' for better compatibility")
    
    print("\n🐧 Linux (Ubuntu/Debian):")
    print("  sudo apt-get install fonts-noto-cjk")
    print("  sudo apt-get install fonts-ipafont")
    print("  sudo apt-get install fonts-takao")
    
    print("\n🐧 Linux (CentOS/RHEL):")
    print("  sudo yum install google-noto-cjk-fonts")
    print("  sudo yum install ipa-gothic-fonts")
    
    print("\n📦 Alternative (pip install):")
    print("  pip install matplotlib[fonts]")
    
    print("\n" + "="*60)

def test_japanese_display():
    """
    Test Japanese text display with a simple plot.
    
    Returns:
        bool: True if test plot was created successfully
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Create a simple test plot
        fig, ax = plt.subplots(figsize=(8, 6))
        
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        
        ax.plot(x, y, label='サイン波')
        ax.set_xlabel('時間 (秒)')
        ax.set_ylabel('電圧 (V)')
        ax.set_title('日本語フォントテスト')
        ax.legend()
        ax.grid(True)
        
        # Save test plot
        test_file = 'japanese_font_test.png'
        plt.savefig(test_file, dpi=100, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Japanese font test plot saved as: {test_file}")
        return True
        
    except Exception as e:
        print(f"❌ Japanese font test failed: {e}")
        return False

# Initialize fonts when module is imported
if __name__ == "__main__":
    # If run directly, perform font setup and testing
    print("Setting up Japanese fonts for matplotlib...")
    selected_font = setup_japanese_fonts()
    print(f"Selected font: {selected_font}")
    
    # Test Japanese display
    if test_japanese_display():
        print("✅ Japanese font configuration successful!")
    else:
        print("❌ Japanese font configuration failed!")
        install_japanese_fonts_guide()
else:
    # If imported, just set up fonts silently
    setup_japanese_fonts()