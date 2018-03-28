# Wavefunction collapse for room generation
# inspiration from : https://github.com/mxgmn/WaveFunctionCollapse
# Each "pixel" is in a superposition of possible pixel values
# In this case, the possible values are indexes into the physical tile table
# as well as the tile palette table.
#
# We first break the input up into n x n tiles, then match the tiles with the
# input, which might be completely blank.
# For each pixel, we store what tiles match in the area surrounding it, and
# the values that the pixel would have if each of those tiles was actually at
# that location.
# The result is a weighted probability distribution over the possible
# pixel values for that location. We then choose to fill the
# *most constrained* pixel by choosing a value from its probability
# distribution. Repeating this process eventually produces a value
# for every pixel (or perhaps leaving a few pixels with no matching tiles)
