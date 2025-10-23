This utility can be used to match distribution probabilities from an optimized feature-game lookup table to a base-game lookup table.

There are several caveats to doing this though, namely: 
- The subset of freegame triggers from the basegame mode must exactly match the featuregame lookup table
- Currently assumes both lookup-tables are already optimized
- Program calculates the required hit-rate of the freegame such that the distribution shape is can be matched. This will override the hit-rate specified in the game-optimization section