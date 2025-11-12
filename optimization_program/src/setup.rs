use serde::Deserialize;

#[derive(Deserialize)]
pub struct SetupConfig {
   pub game_name:String,
   pub bet_type:String,
   pub num_show_pigs:u32,
   pub num_pigs_per_fence:u32,
   pub threads_for_fence_construction:u32,
   pub threads_for_show_construction:u32,
   pub score_type:String,
   pub test_spins:Vec<u32>,
   pub test_spins_weights:Vec<f64>,
   pub simulation_trials:u32,
   pub run_1000_batch:bool,
   pub path_to_games: String,
   pub min_mean_to_median: f64,
   pub max_mean_to_median:f64,
   pub pmb_rtp:f64,
   pub max_trial_dist:u32,
}
