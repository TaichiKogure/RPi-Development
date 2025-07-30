"""
Font Configuration Module

This module provides centralized font configuration for matplotlib to properly
display Japanese characters in the application.
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import warnings
import logging

# Set up logging
logger = logging.getLogger(__name__)

def setup_japanese_fonts():
    """
    Configure matplotlib to use Japanese-compatible fonts.
    
    This function sets up matplotlib to use fonts that can display Japanese
    characters (Hiragana, Katakana, and Kanji) properly, eliminating the
    UserWarning messages about missing glyphs.
    
    Returns:
        str: Name of the font that was successfully configured
    """
    
    # List of Japanese fonts to try, in order of preference
    japanese_fonts = [
        'Yu Gothic',           # Modern, clean Japanese font (Windows 8.1+)
        'MS Gothic',           # Classic Japanese font (widely available)
        'Meiryo',             # Clean, readable Japanese font
        'BIZ UDGothic',       # Business-oriented Japanese font
        'BIZ UDMincho',       # Traditional Japanese font
        'HGGothicM',          # HG Gothic Medium
        'Malgun Gothic',      # Korean font that supports Japanese
        'SimSun',             # Chinese font that supports Japanese
        'DejaVu Sans'         # Fallback to default (will show warnings)
    ]
    
    # Try to find and set a Japanese font
    for font_name in japanese_fonts:
        try:
            # Check if the font is available
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            if font_name in available_fonts:
                # Set the font for matplotlib
                plt.rcParams['font.family'] = font_name
                plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
                
                # Test if the font can render Japanese characters
                test_chars = 'あいうえおアイウエオ漢字'
                fig, ax = plt.subplots(figsize=(1, 1))
                ax.text(0.5, 0.5, test_chars, fontfamily=font_name)
                plt.close(fig)
                
                logger.info(f"Successfully configured Japanese font: {font_name}")
                return font_name
                
        except Exception as e:
            logger.warning(f"Failed to configure font {font_name}: {e}")
            continue
    
    # If no Japanese font was found, suppress font warnings
    logger.warning("No suitable Japanese font found. Font warnings will be suppressed.")
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
    return 'DejaVu Sans'

def get_japanese_font():
    """
    Get the name of the currently configured Japanese font.
    
    Returns:
        str: Name of the Japanese font being used
    """
    return plt.rcParams['font.family'][0] if isinstance(plt.rcParams['font.family'], list) else plt.rcParams['font.family']

def suppress_font_warnings():
    """
    Suppress matplotlib font warnings for missing glyphs.
    
    This is a fallback solution when Japanese fonts are not available.
    """
    warnings.filterwarnings('ignore', category=UserWarning, 
                          message='.*Glyph.*missing from font.*')
    logger.info("Font warnings suppressed")

def configure_matplotlib_japanese():
    """
    Main function to configure matplotlib for Japanese text display.
    
    This function should be called once at the start of the application
    to set up proper Japanese font support.
    
    Returns:
        dict: Configuration result with font name and status
    """
    try:
        font_name = setup_japanese_fonts()
        
        # Additional matplotlib settings for better Japanese text rendering
        plt.rcParams['axes.unicode_minus'] = False  # Use ASCII minus sign
        plt.rcParams['figure.autolayout'] = True    # Better layout for Japanese text
        
        return {
            'success': True,
            'font': font_name,
            'message': f'Japanese font configured: {font_name}'
        }
        
    except Exception as e:
        logger.error(f"Failed to configure Japanese fonts: {e}")
        suppress_font_warnings()
        
        return {
            'success': False,
            'font': 'DejaVu Sans',
            'message': f'Font configuration failed, warnings suppressed: {e}'
        }

# Auto-configure when module is imported
if __name__ != '__main__':
    try:
        result = configure_matplotlib_japanese()
        if result['success']:
            logger.info(result['message'])
        else:
            logger.warning(result['message'])
    except Exception as e:
        logger.error(f"Auto-configuration failed: {e}")

# Test function for debugging
def test_japanese_font():
    """
    Test function to verify Japanese font configuration.
    
    This function creates a test plot with Japanese text to verify
    that the font configuration is working properly.
    """
    import matplotlib.pyplot as plt
    
    # Test Japanese text
    test_texts = [
        "シミュレーション結果がここに表示されます",
        "dQ/dV曲線がここに表示されます", 
        "機械学習結果がここに表示されます",
        "テスト用の日本語テキスト：ひらがな、カタカナ、漢字"
    ]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for i, text in enumerate(test_texts):
        ax.text(0.1, 0.8 - i*0.2, text, fontsize=12, transform=ax.transAxes)
    
    ax.set_title("Japanese Font Test", fontsize=14)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print(f"Current font: {get_japanese_font()}")

if __name__ == '__main__':
    # Run test when script is executed directly
    print("Testing Japanese font configuration...")
    result = configure_matplotlib_japanese()
    print(f"Configuration result: {result}")
    test_japanese_font()