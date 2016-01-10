# PyRain
Replay Analysis Interface  
This project aims to provide a graphical analysis of matches from Rocketleague replay files. The replay parsing is done with pyrope (https://github.com/Galile0/pyrope)

# Features
* Display of Metadata
* Plotting Heatmaps for Players, either based on a whole match or seperated by Goals
    * Heatmaps as Hexbin, 2D Histogram, Interpolated 2D Histogram
    * Optional logarithmic scaling of values to keep rare positions visible against common positions (like kickoff spawn)
    * Dynamically set resolution of the heatmap
* Distance Plotting, graphical representation of ball chasers...or were you the one?! :O
* Exporting Images (Currently only Exporting a single image at a time, no dynamic subplots as of yet)

# Installation

## From binary
Binaries are Windows only currently. In theory it should run on every Version (7/10 32/64 Bit) but I didn't had the patience to setup a VM for each combination and test it myself. So try it out and report errors you may encounter
To get the latest Release go to the release tab of this github repo and grab the latest binary zip. Just run the pyrain.exe and you should be good to go.

## From source
* Clone repository
* install requirements (Grab pyrope from my other repo, its not on pypi yet)
* run pyrain_gui.py

# Known Bugs
* Mutators will produce errors. This is a missing feature of pyrope, the replay parsing lib

# In the works
* Some kind of 3D visualization
    Not yet decided on a useful representation
* More Non graphical data like:
    * Missed shots
    * Boost efficiency
    * Area Coverage
    * Airtime
    * Hitting strength
    
Got ideas? Shoot me a mail or open an issue here. Please only consider the following: If you have an idea, make sure you can define exactly what you want. Suggestions like "You should show who was the best player" without saying what defines *best* is pretty useless.

