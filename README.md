# Rosetta Stone 3D Print

**[Download the 900 mm, 12-panel Bambu Studio project](print/02%20-%20Rosetta%20900%20mm%20-%20bow-tie%20panels.3mf)**

Use a **Bambu Lab P1S with a 0.4 mm nozzle** and map AMS filament **1 to black PLA** and **2 to white PLA**. The assembled display measures approximately 900 × 664 mm. All three inscription sections have recessed lettering with white groove floors.

## Print

1. Open the panel project in Bambu Studio. Select your build plate and PLA presets and keep the project's 0.12 mm layer height. The panels are arranged face up with the rear key pockets against the bed.
2. Slice the plates with your printer setup. In Preview, use the Filament colour scheme to check each panel's bed placement and white groove floors. The supplied profile uses the purge chute with the prime tower disabled. The white band spans two layers and uses two colour changes per panel.
3. Print each panel and label the back with its row and column before setting it aside. Print the matching [bow-tie key plate](print/03%20-%20Bow-tie%20keys.3mf).

**Optional first print.** Use the [bow-tie joint fit test](print/01%20-%20Bow-tie%20joint%20fit%20test.3mf) to check the seam, key fit and white floor before printing the full set. Remove any first-layer lip or loose bridge strands, bring the two halves together and press the key into the shared recess from the rear. It should sit below the back surface and catch on both halves when seated. Turn the sample over to check that the front faces sit flush and the white is clean.

## Assemble

1. Lay out the panels using the [numbered front diagram](docs/Assembly%20diagram.png). Viewed from the front, R1 is the top row and C1 is the left column.
2. Use the [rear pocket layout](docs/Rear%20key%20layout.png) and [bow-tie key diagram](docs/How%20the%20bow-tie%20key%20locks.png) to fit the keys across the seams. Dry-fit the entire set. Hold the seams closed and align any inscription strokes that cross a joint. White exposed on a cut edge should sit inside the closed seam.
3. For wall display, bond the panels to a rigid backing board with adhesive compatible with PLA and the board. The board captures the keys and carries the weight. Attach hanging hardware to the board and size it for the finished assembly and wall.

## Other slicers

Download [Row 1](stl/Row%201.zip), [Row 2](stl/Row%202.zip), [Row 3](stl/Row%203.zip), [Row 4](stl/Row%204.zip), and the [keys and optional fit samples](stl/Keys%20and%20fit%20test.zip). Import each panel's black and white STLs together as parts of one object, preserving their relative positions. Assign the two filaments and place the panel face up. The [assembly coordinates](docs/Assembly%20data.json) accompany the meshes.

## Fidelity and license

This display adapts the Florida–Leipzig depth map with a traced outline, flattened inscription field and a flat back with recessed key pockets. The modeled cuts are 1.56 mm deep. Fine source marks may be lost during extraction, and individual strokes can vary in legibility when printed.

Adapted from *Depth map of the Rosetta Stone* (2018) by Amin, Barmpoutis, Berti, Bozia, Hensel and Naether, University of Florida and Leipzig University. The depth data and derived geometry are shared under [CC BY-NC-SA 4.0](SOURCE-LICENSE.md). [Original dataset](https://github.com/digitalepigraphy/RosettaStone)

[Maintainer notes, source files and validation records](docs/Maintainers.md)
