# Japanese Font Configuration Guide

## Overview

This guide explains the Japanese font configuration solution implemented to resolve matplotlib UserWarning messages about missing Japanese glyphs (Hiragana, Katakana, and Kanji characters).

## Problem Description

The application was displaying numerous UserWarning messages like:
```
UserWarning: Glyph 12471 (\N{KATAKANA LETTER SI}) missing from font(s) DejaVu Sans.
UserWarning: Glyph 32080 (\N{CJK UNIFIED IDEOGRAPH-7D50}) missing from font(s) DejaVu Sans.
```

These warnings occurred because matplotlib's default font (DejaVu Sans) doesn't support Japanese characters, but the application displays Japanese text in several locations:

- **simulation_tab.py:175** - "シミュレーション結果がここに表示されます" (Simulation results will be displayed here)
- **analysis_tab.py:206** - "dQ/dV曲線がここに表示されます" (dQ/dV curves will be displayed here)  
- **ml_tab.py:222** - "機械学習結果がここに表示されます" (Machine learning results will be displayed here)

## Solution Implementation

### 1. Centralized Font Configuration Module

Created `font_config.py` that provides:

- **Automatic font detection**: Searches for available Japanese fonts on the system
- **Font priority list**: Uses the best available Japanese font in order of preference:
  1. Yu Gothic (modern, clean)
  2. MS Gothic (classic, widely available)
  3. Meiryo (clean, readable)
  4. BIZ UDGothic (business-oriented)
  5. BIZ UDMincho (traditional)
  6. HGGothicM (HG Gothic Medium)
  7. Malgun Gothic (Korean font with Japanese support)
  8. SimSun (Chinese font with Japanese support)
- **Fallback mechanism**: Suppresses warnings if no Japanese fonts are available
- **Auto-configuration**: Automatically configures matplotlib when imported

### 2. Integration with Tab Modules

Updated the following files to import the font configuration:

- `simulation_tab.py` - Added `import font_config`
- `analysis_tab.py` - Added `import font_config`  
- `ml_tab.py` - Added `import font_config`

The font configuration is automatically applied when these modules are imported.

### 3. Additional Matplotlib Settings

The configuration also applies these settings for better Japanese text rendering:

```python
plt.rcParams['axes.unicode_minus'] = False  # Use ASCII minus sign
plt.rcParams['figure.autolayout'] = True    # Better layout for Japanese text
```

## Testing and Verification

### Test Results

The solution was verified using `test_font_fix.py`:

```
✅ ALL TESTS PASSED - Japanese font configuration is working!
✓ Font configuration imported successfully
✓ Current font: Yu Gothic
✓ Japanese text rendered successfully
✅ No font warnings detected!
✅ No font warnings during module imports!
```

### Manual Testing

To manually test the font configuration:

```bash
python font_config.py
```

This will display a test window with Japanese text using the configured font.

## Font Configuration Details

### Available Japanese Fonts (System Dependent)

The following Japanese fonts were detected on the test system:

- BIZ UDGothic, BIZ UDMincho
- MS Gothic, MS Mincho  
- Yu Gothic, Yu Mincho
- Meiryo
- HGGothicE, HGGothicM, HGMaruGothicMPRO, HGMinchoB, HGMinchoE, HGSoeiKakugothicUB
- Malgun Gothic
- SimSun, SimSun-ExtB, SimSun-ExtG

### Font Selection Logic

The `setup_japanese_fonts()` function:

1. Iterates through the priority list of Japanese fonts
2. Checks if each font is available on the system
3. Tests the font by rendering Japanese characters
4. Sets the first working font as the default
5. Falls back to warning suppression if no Japanese fonts work

### Configuration Functions

- `configure_matplotlib_japanese()` - Main configuration function
- `setup_japanese_fonts()` - Font detection and setup
- `get_japanese_font()` - Returns currently configured font name
- `suppress_font_warnings()` - Fallback warning suppression
- `test_japanese_font()` - Test function for debugging

## Maintenance

### Adding New Japanese Text

When adding new Japanese text to matplotlib plots:

1. Ensure the module imports `font_config`
2. The text will automatically use the configured Japanese font
3. No additional configuration is needed

### Troubleshooting

If font warnings still appear:

1. Check that `font_config` is imported in the affected module
2. Verify Japanese fonts are available: `python -c "import font_config; print(font_config.get_japanese_font())"`
3. Run the test: `python test_font_fix.py`
4. Check logs for font configuration messages

### System Requirements

- **Windows**: Usually has MS Gothic, Yu Gothic, or Meiryo pre-installed
- **macOS**: May need to install Japanese fonts manually
- **Linux**: Install fonts like `fonts-noto-cjk` or `fonts-takao`

### Installing Japanese Fonts (if needed)

**Windows:**
```bash
# Usually pre-installed, but if needed:
# Install from Windows Features or download from Microsoft
```

**macOS:**
```bash
# Install Noto fonts
brew install font-noto-sans-cjk-jp
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install fonts-noto-cjk fonts-takao-gothic fonts-takao-mincho
```

## Files Modified

1. **Created:**
   - `font_config.py` - Centralized font configuration module
   - `test_font_fix.py` - Test script for verification
   - `FONT_CONFIGURATION_GUIDE.md` - This documentation

2. **Modified:**
   - `simulation_tab.py` - Added font_config import
   - `analysis_tab.py` - Added font_config import
   - `ml_tab.py` - Added font_config import

## Benefits

- ✅ Eliminates all Japanese font warnings
- ✅ Proper display of Japanese characters in plots
- ✅ Automatic font detection and configuration
- ✅ Fallback mechanism for systems without Japanese fonts
- ✅ Centralized, maintainable solution
- ✅ No changes needed to existing Japanese text

## Future Considerations

- The font configuration is applied globally to matplotlib
- New modules with Japanese text should import `font_config`
- Consider adding font preference settings to user configuration
- Monitor for new Japanese fonts that could be added to the priority list