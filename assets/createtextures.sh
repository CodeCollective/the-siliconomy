#!/bin/bash

# Create textures directory if it doesn't exist
mkdir -p textures

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "ImageMagick is required but not installed. Install with:"
    echo "Ubuntu/Debian: sudo apt install imagemagick"
    echo "macOS: brew install imagemagick"
    echo "Fedora/RHEL: sudo dnf install ImageMagick"
    exit 1
fi

echo "Creating basic textures for laser cutter model..."

# Metal texture - brushed aluminum look
convert -size 512x512 xc:gray70 \
    -attenuate 0.3 +noise Uniform \
    -blur 0x0.5 \
    -motion-blur 0x20+0 \
    -normalize \
    -modulate 100,50,100 \
    textures/metal.jpg

echo "Created metal.jpg"

# Aluminum texture - lighter, more reflective
convert -size 512x512 xc:gray85 \
    -attenuate 0.2 +noise Uniform \
    -blur 0x0.3 \
    -motion-blur 0x15+0 \
    -normalize \
    -modulate 100,30,110 \
    textures/aluminum.jpg

echo "Created aluminum.jpg"

# Steel texture - darker, industrial look
convert -size 512x512 xc:gray50 \
    -attenuate 0.4 +noise Uniform \
    -blur 0x0.5 \
    -motion-blur 0x25+45 \
    -normalize \
    -modulate 100,70,90 \
    textures/steel.jpg

echo "Created steel.jpg"

# Rail texture - metallic with linear pattern
convert -size 512x512 xc:gray60 \
    \( -size 512x512 pattern:hs_vertical -blur 1x0 \) \
    -compose multiply -composite \
    -attenuate 0.3 +noise Uniform \
    -normalize \
    textures/rail.jpg

echo "Created rail.jpg"

# Panel texture - matte plastic/metal
convert -size 512x512 xc:gray75 \
    -attenuate 0.15 +noise Uniform \
    -blur 0x1 \
    -normalize \
    -modulate 100,20,95 \
    textures/panel.jpg

echo "Created panel.jpg"

# Button texture - plastic with slight gloss
convert -size 128x128 xc:gray80 \
    -attenuate 0.1 +noise Uniform \
    -blur 0x0.5 \
    -normalize \
    -modulate 100,40,105 \
    textures/button.jpg

echo "Created button.jpg"

# Cable texture - black rubber/plastic
convert -size 256x256 xc:gray20 \
    -attenuate 0.2 +noise Uniform \
    -blur 0x0.5 \
    -normalize \
    -modulate 100,10,80 \
    textures/cable.jpg

echo "Created cable.jpg"

# Lens texture - glass/transparent look (actually just a light gray)
convert -size 256x256 xc:gray90 \
    -attenuate 0.05 +noise Uniform \
    -blur 0x0.2 \
    -normalize \
    -modulate 100,5,110 \
    textures/lens.png

echo "Created lens.png"

# LCD texture - dark screen with slight reflection
convert -size 256x128 xc:gray15 \
    -attenuate 0.1 +noise Uniform \
    -blur 0x0.3 \
    -normalize \
    -modulate 100,20,85 \
    textures/lcd.png

echo "Created lcd.png"

# Logo texture - simple white background for text
convert -size 512x128 xc:white \
    -attenuate 0.02 +noise Uniform \
    -normalize \
    textures/logo.png

echo "Created logo.png"

echo ""
echo "All textures created successfully in the 'textures' directory!"
echo ""
echo "Generated files:"
ls -la textures/

echo ""
echo "Texture descriptions:"
echo "- metal.jpg: Brushed metal finish for main enclosure"
echo "- aluminum.jpg: Light aluminum for cutting bed"
echo "- steel.jpg: Dark steel for laser components"
echo "- rail.jpg: Linear pattern for rails"
echo "- panel.jpg: Matte finish for control panel"
echo "- button.jpg: Plastic texture for buttons"
echo "- cable.jpg: Dark rubber for cables"
echo "- lens.png: Glass-like for laser lens"
echo "- lcd.png: Dark screen for display"
echo "- logo.png: White background for branding"