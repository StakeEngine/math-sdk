use exes::IdentityCondition;
use ndarray::{s, Array1};
use rand::prelude::*;
use rand::Rng;
use rand_distr::{Distribution, WeightedIndex};
use rayon::prelude::*;
use core::panic;
use std::hash::{Hash, Hasher};
use std::mem;
use std::path::{Path};
use std::{
    cmp::Ordering, collections::HashMap, fs, fs::File, io::BufWriter, io::Write,
    time::Instant,
};

mod setup;
use setup::SetupConfig;

mod exes;
use exes::{
    load_config_data, load_force_options, read_look_up_table, DressJson, FenceJson,
    LookUpTableEntry, SearchResult
};

use crate::exes::BiasJson;
// use flame;

fn main() {
    // Read the contents of the file
    let now = Instant::now();
    let cont = fs::read_to_string("src/setup.toml").expect("cannot find setup file in src/");
    let config: SetupConfig = toml::from_str(&cont).expect("failed to parse setup file");
    
    run_farm(
        &config.game_name,
        &config.bet_type,
        config.num_show_pigs,
        config.num_pigs_per_fence,
        config.threads_for_fence_construction,
        config.threads_for_show_construction,
        &config.test_spins,
        &config.test_spins_weights,
        config.simulation_trials,
        config.run_1000_batch,
        &config.path_to_games,
        config.min_mean_to_median,
        config.max_mean_to_median,
        config.pmb_rtp,
        config.max_trial_dist,
    );
    println!("time taken {}ms", now.elapsed().as_secs());
}

fn run_farm(
    game_name: &str,
    bet_type: &str,
    num_show_pigs: u32,
    num_pigs_per_fence: u32,
    threads_for_fence_construction: u32,
    threads_for_show_construction: u32,
    test_spins: &Vec<u32>,
    test_spins_weights: &Vec<f64>,
    simulation_trials: u32,
    run_1000_batch: bool,
    path_to_games: &str,
    min_mean_to_median: f64,
    max_mean_to_median: f64,
    pmb_rtp: f64,
    max_trial_dist: u32,
) {
    println!("Running Simulations: {} - Mode: {}", game_name, bet_type);

    // LOAD IN FORCE OPTIONS AND CONFIG FILE
    let force_options = load_force_options(game_name, bet_type, path_to_games.to_string());
    
    let config_file: exes::ConfigData;
    config_file = load_config_data(game_name, path_to_games.to_string());
    let bet_mode_index = config_file.bet_modes.iter().position(|bm| bm.bet_mode == bet_type).expect("betmode index not found in betmode summary array");
    let fence_index = config_file.fences.iter().position(|fi| fi.bet_mode == bet_type).expect("betmode not found in fences array");
    let dress_index = config_file.dresses.iter().position(|di|di.bet_mode == bet_type).expect("betmode not found in dress array");
    let bias_index = config_file.bias.iter().position(|bi| bi.bet_mode == bet_type).expect("betmode not found in bias array");

    let mut lookup_table = match read_look_up_table(game_name, bet_type, path_to_games.to_string())
    {
        Ok(table) => table,
        Err(err) => {
            eprintln!("Error reading the CSV file: {}", err);
            return;
        }
    };
    let init_lookup = lookup_table.clone();
    // NOW WE WANT TO GET A VECTOR CONTAINING ALL THE SORTED WINS
    let mut sorted_wins: Vec<f64> = Vec::new();
    let bet_amount = config_file.bet_modes[bet_mode_index].cost;
    let rtp = config_file.bet_modes[bet_mode_index].rtp;
    let mut total_prob = 0.0;
    let mut fences: Vec<Fence> = Vec::new();

    // FIRST THING WE HAVE TO DO IS CREATE EACH FENCE FOR PIGS
    for fence in &config_file.fences[fence_index].fences {
        fences.push(parse_fence_info(
            fence,
            &mut total_prob,
            bet_amount,
            &&config_file.dresses[dress_index].dresses,
        ));
    }
    // NOW NEED TO APPLY THE HR TO "x" and generate Pigs for Fence
    let mut pig_pens: Vec<Vec<Pig>> = Vec::with_capacity(fences.len());
    for mut fence in &mut fences {
        if fence.hr == -1.0 {
            fence.hr = 1.0 / (1.0 - total_prob);
            fence.avg_win = fence.hr * fence.rtp;
        }
        println!("\nCreating {} Fence\n", fence.name);
        sort_wins_by_parameter(&mut fence, &force_options, &mut lookup_table);

        let bias_betmode: Vec<BiasJson> = config_file.bias[bias_index].bias.clone();
        let mut bias_fence: Option<BiasJson> = None;
        for b in bias_betmode.iter() {
            if b.criteria == fence.name {
                bias_fence = Some(b.clone());
                break;
            }
        }


        if !fence.win_type {
            let mut win_range_params: Vec<&mut Dress> = Vec::new();
            for dress in &mut fence.dresses {
                win_range_params.push(dress);
            }
            let mut win_array: Vec<f64> = Vec::with_capacity(fence.win_dist.keys().len());
            for win in fence.win_dist.keys() {
                win_array.push(win.0);

                if !sorted_wins.contains(&win.0) {
                    sorted_wins.push(win.0);
                }
            }
            win_array.sort_by(|a, b| a.partial_cmp(b).unwrap());
            let max_win = win_array[win_array.len() - 1];
            let min_win = win_array[0];

            let pig_heaven = PigHeaven {
                bet_amount: bet_amount,
                wins: win_array,
                rtp: fence.rtp,
                pig_params: win_range_params,
                num_pigs: num_pigs_per_fence / threads_for_fence_construction,
                max_win: max_win,
                min_win: min_win,
                avg_win: fence.avg_win * bet_amount,
            };
            let thread_pool = rayon::ThreadPoolBuilder::new()
                .num_threads(threads_for_fence_construction as usize)
                .build()
                .unwrap();

            // Use Rayon's par_bridge method to process x1 and x2 concurrently
            let fence_pigs: Vec<Pig> = thread_pool.install(|| {
                (0..threads_for_fence_construction)
                    .into_par_iter()
                    .flat_map(|_| {
                        create_ancestors(
                            &pig_heaven,
                            fence.min_mean_to_median,
                            fence.max_mean_to_median,
                            bias_fence.clone().unwrap_or(BiasJson {
                                criteria: "".to_string(),
                                range: [0.0, 0.0],
                                prob: 0.0,
                            }),
                            max_trial_dist,
                        )
                    })
                    .collect()
            });
            pig_pens.push(fence_pigs);
        } else {
            const EPSILON: f64 = 1e-9;
            if !init_lookup.values().any(|entry| (entry.win - fence.avg_win).abs() < EPSILON) {
                panic!(
                    "fence.avg_win {} not found in lookup table",
                    fence.avg_win
                );
            }
}           
            sorted_wins.push(fence.avg_win);
    }

    sorted_wins.sort_by(|a, b| a.partial_cmp(&b).unwrap());

    let sorted_wins_array = Array1::from_vec(sorted_wins);

    let thread_pool_show_pigs = rayon::ThreadPoolBuilder::new()
        .num_threads(threads_for_show_construction as usize)
        .build()
        .unwrap();
    let mut show_pigs: Vec<ShowPig> = thread_pool_show_pigs.install(|| {
        (0..threads_for_show_construction)
            .into_par_iter()
            .flat_map(|thread_index| {
                create_show_pigs(
                    &fences,
                    num_show_pigs / threads_for_show_construction,
                    test_spins,
                    test_spins_weights,
                    simulation_trials,
                    bet_amount,
                    thread_index,
                    &sorted_wins_array,
                    &pig_pens,
                    rtp,
                    min_mean_to_median,
                    max_mean_to_median,
                    pmb_rtp,
                )
            })
            .collect()
    });
    show_pigs.sort_by(|a, b| b.success_score.partial_cmp(&a.success_score).unwrap());

    print_information(
        &show_pigs,
        &fences,
        simulation_trials,
        &sorted_wins_array,
        bet_amount,
        test_spins,
        &pig_pens,
        game_name.to_string(),
        bet_type.to_string(),
        path_to_games.to_string(),
        pmb_rtp,
    );
}

fn print_information(
    show_pigs: &Vec<ShowPig>,
    fences: &Vec<Fence>,
    trials: u32,
    sorted_wins: &Array1<f64>,
    bet_amount: f64,
    test_spins: &Vec<u32>,
    pig_pens: &Vec<Vec<Pig>>,
    game_name: String,
    bet_type: String,
    path_to_games: String,
    pmb_rtp: f64,
) {
    let mut win_dist_index_map: HashMap<F64Wrapper, usize> =
        HashMap::with_capacity(sorted_wins.len());
    let mut count: usize = 0;

    for win in sorted_wins {
        win_dist_index_map.insert(F64Wrapper(win.clone()), count);
        count += 1;
    }
    let num_pigs = 10;

    (0..num_pigs).into_par_iter().for_each(|pig_index| {
        println!("Printing info for Distribution {}", pig_index + 1);
        let mut lookup_table: HashMap<u32, LookUpTableEntry> =
            match read_look_up_table(&game_name, &bet_type, path_to_games.to_string()) {
                Ok(table) => table,
                Err(err) => {
                    eprintln!("Error reading the CSV file: {}", err);
                    return;
                }
            };
        let (succuss_vals, weights, wins_for_fences, weights_from_pigs) = recreate_show_pig(
            &show_pigs[pig_index],
            fences,
            trials,
            sorted_wins,
            bet_amount,
            test_spins,
            pig_pens,
            &win_dist_index_map,
            pmb_rtp,
        );
        {
            let file_path = Path::new(&path_to_games)
                .join(game_name.clone())
                .join("library")
                .join("optimization_files")
                .join(format!("{}_0_{}.csv", bet_type, pig_index + 1));
            let mut file = BufWriter::new(File::create(file_path).unwrap());
            for (_index, value) in succuss_vals.iter().enumerate() {
                if _index == succuss_vals.len() - 1 {
                    write!(file, "{}", value).expect("Failed to write to file");
                } else {
                    write!(file, "{}, ", value).expect("Failed to write to file");
                }
            }
        }
        let mut non_win_fence_count: usize = 0;
        for fence in fences {
            if fence.win_type {
                for (index, book_id_list) in &fence.win_dist {
                    for book_id in book_id_list {
                        lookup_table.entry(*book_id).and_modify(|value| {
                            value.weight = ((1.0 / fence.hr / (book_id_list.len() as f64))
                                * (2_f64.powf(50.0) as f64))
                                as u64;
                        });
                    }
                }
            } else {
                for (win, book_id_list) in &fence.win_dist {
                    let mut weight = 0.0;
                    for win_index in 0..wins_for_fences[non_win_fence_count].len() {
                        if (wins_for_fences[non_win_fence_count][win_index] - win.0).powi(2)
                            < 0.000000000000000000001
                        {
                            weight = weights_from_pigs[non_win_fence_count][win_index]
                                / fence.hr
                                / (book_id_list.len() as f64);
                            break;
                        }
                    }
                    for book_id in book_id_list {
                        lookup_table.entry(*book_id).and_modify(|value| {
                            value.weight = (weight * (2_f64.powf(50.0) as f64)) as u64;
                        });
                    }
                }
                non_win_fence_count += 1;
            }
        }
        let mut rtp = 0.0;
        let mut sum_dist = 0.0;
        let mut sorted_indexes: Vec<&u32> = lookup_table.keys().into_iter().collect();
        sorted_indexes.sort();

        for index in &sorted_indexes {
            let entry = lookup_table.get(index).unwrap();
            rtp += entry.weight as f64 * entry.win;
            sum_dist += entry.weight as f64;
        }
        rtp = rtp / sum_dist;
        if pig_index == 0 {
            {
                let file_path = Path::new(&path_to_games)
                    .join(&game_name)
                    .join("library")
                    .join("publish_files")
                    .join(format!("lookUpTable_{}_0.csv", bet_type));

                let mut file = BufWriter::new(File::create(file_path).unwrap());
                for index in &sorted_indexes {
                    let entry = lookup_table.get(index).unwrap();
                    let rounded_win = (entry.win * 100.0).round(); //format!("{:.2}", entry.win);
                    write!(file, "{},{},{}\n", entry.id, entry.weight, rounded_win as u64)
                        .expect("Failed to write to file");
                }
            }
        }
        {
            let file_path = Path::new(&path_to_games)
                .join(&game_name)
                .join("library")
                .join("optimization_files")
                .join(format!("{}_0_{}.csv", bet_type, pig_index + 1));
            let mut file = BufWriter::new(File::create(file_path).unwrap());
            write!(file, "Name,Pig{}\n", (pig_index + 1)).expect("Failed to write to file");
            write!(file, "Score,{}\n", show_pigs[pig_index].success_score)
                .expect("Failed to write to file");
            write!(file, "LockedUpRTP,\n").expect("Failed to write to file");
            write!(file, "Rtp,{}\n", rtp).expect("Failed to write to file");
            write!(file, "Win Ranges\n").expect("error");
            get_win_ranges(&mut file, &weights, sorted_wins);
            write!(file, "Distribution\n").expect("Failed to write to file");
            for index in &sorted_indexes {
                let entry = lookup_table.get(index).unwrap();
                let rounded_win = format!("{:.2}", entry.win);
                write!(file, "{},{},{}\n", entry.id, entry.weight, rounded_win)
                    .expect("Failed to write to file");
            }
        }
    });

}

fn get_win_ranges<T: std::io::Write>(
    file: &mut T,
    weights: &Array1<f64>,
    sorted_wins: &Array1<f64>,
) {
    let mut win_ranges: Vec<((f64, f64), f64)> = vec![
        ((0.0, 0.1), 0.0),
        ((0.1, 1.0), 0.0),
        ((1.0, 2.0), 0.0),
        ((2.0, 3.0), 0.0),
        ((3.0, 5.0), 0.0),
        ((5.0, 10.0), 0.0),
        ((10.0, 20.0), 0.0),
        ((20.0, 50.0), 0.0),
        ((50.0, 100.0), 0.0),
        ((100.0, 200.0), 0.0),
        ((200.0, 500.0), 0.0),
        ((500.0, 1000.0), 0.0),
        ((1000.0, 2000.0), 0.0),
        ((2000.0, 3000.0), 0.0),
        ((3000.0, 5001.0), 0.0)
    ];
    for win_index in 0..sorted_wins.len() {
        for range_index in 0..win_ranges.len() {
            let ((low, high), tot) = win_ranges[range_index];
            if sorted_wins[win_index] >= low && sorted_wins[win_index] < high {
                win_ranges[range_index] = ((low, high), tot + weights[win_index]);
            }
        }
    }
    for ((low, high), tot) in win_ranges {
        if tot == 0.0 {
            write!(file, "{},{},1 in never\n", low, high).expect("failed");
        } else {
            let prob = 1.0 / tot;
            write!(file, "{},{},1 in {:.3}\n", low, high, prob).expect("failed");
        }
    }
}

fn recreate_show_pig(
    show_pig: &ShowPig,
    fences: &Vec<Fence>,
    trials: u32,
    sorted_wins: &Array1<f64>,
    bet_amount: f64,
    test_spins: &Vec<u32>,
    pig_pens: &Vec<Vec<Pig>>,
    win_dist_index_map: &HashMap<F64Wrapper, usize>,
    pmb_rtp: f64,
) -> (Vec<f64>, Array1<f64>, Vec<Vec<f64>>, Vec<Vec<f64>>) {
    let mut weights: Array1<f64> = Array1::from_vec(vec![0.0; sorted_wins.len()]);
    let mut wins_for_fences: Vec<Vec<f64>> = Vec::new();
    let mut weights_from_pigs: Vec<Vec<f64>> = Vec::new();
    let mut random_weights_to_apply: Vec<Vec<Vec<f64>>> = Vec::new();
    for fence in fences {
        if !fence.win_type {
            let mut _win_vec: Vec<f64> = Vec::with_capacity(fence.win_dist.len());
            for (key, _win) in &fence.win_dist {
                _win_vec.push(key.0);
            }
            _win_vec.sort_by(|a, b| a.partial_cmp(&b).unwrap());
            wins_for_fences.push(_win_vec);
            weights_from_pigs.push(vec![0.0; fence.win_dist.len()]);
            random_weights_to_apply.push(Vec::new());
        }
    }
    let mut non_win_type_count: usize = 0;
    for fence in fences {
        if fence.win_type {
            if let Some(index) = win_dist_index_map.get(&F64Wrapper(fence.avg_win)) {
                weights[*index] += 1.0 / fence.hr;
            }
        } else {
            random_weights_to_apply[non_win_type_count].push(vec![
                0.0;
                wins_for_fences
                    [non_win_type_count]
                    .len()
            ]);
            random_weights_to_apply[non_win_type_count].push(vec![
                0.0;
                wins_for_fences
                    [non_win_type_count]
                    .len()
            ]);

            let pig_index = show_pig.pig_indexes[non_win_type_count];
            let random_pig = &pig_pens[non_win_type_count][pig_index];
            get_weights(
                &wins_for_fences[non_win_type_count],
                &mut weights_from_pigs[non_win_type_count],
                &random_pig.amps,
                &random_pig.mus,
                &random_pig.stds,
                &random_pig.params,
                &random_pig.apply_parms,
                &random_pig.random_seeds,
                &random_pig.random_weights,
                &random_pig.random_apply_params,
                &mut random_weights_to_apply[non_win_type_count],
            );

            let mut n = 0;
            while n < weights_from_pigs[non_win_type_count].len() {
                if let Some(index) =
                    win_dist_index_map.get(&F64Wrapper(wins_for_fences[non_win_type_count][n]))
                {
                    weights[*index] += weights_from_pigs[non_win_type_count][n] / fence.hr;
                    // norm_factor +=  weights_from_pigs[non_win_type_count][n]/fence.hr;
                }
                n += 1;
            }
            non_win_type_count += 1;
        }
    }
    let mut rtp = 0.0;
    for index in 0..sorted_wins.len() {
        rtp += sorted_wins[index] * weights[index]
    }
    let success = run_enhanced_simulation(
        &sorted_wins,
        &weights,
        test_spins[test_spins.len() - 1usize] as usize,
        trials as usize,
        bet_amount,
        test_spins,
        pmb_rtp,
    );

    return (success, weights, wins_for_fences, weights_from_pigs);
}

fn create_show_pigs(
    fences: &Vec<Fence>,
    num_pigs: u32,
    test_spins: &Vec<u32>,
    test_spins_weights: &Vec<f64>,
    trials: u32,
    bet_amount: f64,
    process_id: u32,
    sorted_wins: &Array1<f64>,
    pig_pens: &Vec<Vec<Pig>>,
    rtp: f64,
    min_mean_to_median: f64,
    max_mean_to_median: f64,
    pmb_rtp: f64,
) -> Vec<ShowPig> {
    println!("Creating Initial Distributions");
    let mut best_score = 0.0;
    let mut rng = rand::thread_rng();
    let mut show_pigs: Vec<ShowPig> = Vec::with_capacity(num_pigs as usize);
    // First Construct the has map
    let mut win_dist_index_map: HashMap<F64Wrapper, usize> =
        HashMap::with_capacity(sorted_wins.len());
    let mut count: usize = 0;
    for win in sorted_wins {
        win_dist_index_map.insert(F64Wrapper(win.clone()), count);
        count += 1;
    }
    let mut weights: Array1<f64> = Array1::from_vec(vec![0.0; sorted_wins.len()]);
    // need to construct wins for each fence
    let mut wins_for_fences: Vec<Vec<f64>> = Vec::new();
    let mut weights_from_pigs: Vec<Vec<f64>> = Vec::new();
    let mut random_weights_to_apply: Vec<Vec<Vec<f64>>> = Vec::new();
    let mut banks: Array1<f64> =
        Array1::zeros((test_spins[test_spins.len() - 1] * trials) as usize);
    for fence in fences {
        if !fence.win_type {
            let mut _win_vec: Vec<f64> = Vec::with_capacity(fence.win_dist.len());
            for (key, _win) in &fence.win_dist {
                _win_vec.push(key.0);
            }
            _win_vec.sort_by(|a, b| a.partial_cmp(&b).unwrap());
            wins_for_fences.push(_win_vec);
            weights_from_pigs.push(vec![0.0; fence.win_dist.len()]);
            random_weights_to_apply.push(Vec::new());
        }
    }

    for p in 0..num_pigs {
        let mut score = 0.0;
        let mut pig_indexes: Vec<usize> = Vec::new();
        for w_index in 0..weights.len() {
            weights[w_index] = 0.0;
        }

        pig_indexes = Vec::new();
        if (p + 1) % (num_pigs / 2) == 0 {
            println!(
                "Thread {}: {}% done",
                process_id,
                100f32 * ((p + 1) as f32) / (num_pigs as f32)
            );
        }
        let mut non_win_type_count: usize = 0;
        for fence in fences {
            if fence.win_type {
                if let Some(index) = win_dist_index_map.get(&F64Wrapper(fence.avg_win)) {
                    weights[*index] += 1.0 / fence.hr;
                } 
            } else {
                if p == 0 {
                    random_weights_to_apply[non_win_type_count].push(vec![
                        0.0;
                        wins_for_fences
                            [non_win_type_count]
                            .len()
                    ]);
                    random_weights_to_apply[non_win_type_count].push(vec![
                        0.0;
                        wins_for_fences
                            [non_win_type_count]
                            .len()
                    ]);
                }
                let pig_index = rng.gen_range(0..=pig_pens[non_win_type_count].len() - 1) as usize;
                pig_indexes.push(pig_index);
                let random_pig = &pig_pens[non_win_type_count][pig_index];
                get_weights(
                    &wins_for_fences[non_win_type_count],
                    &mut weights_from_pigs[non_win_type_count],
                    &random_pig.amps,
                    &random_pig.mus,
                    &random_pig.stds,
                    &random_pig.params,
                    &random_pig.apply_parms,
                    &random_pig.random_seeds,
                    &random_pig.random_weights,
                    &random_pig.random_apply_params,
                    &mut random_weights_to_apply[non_win_type_count],
                );

                let mut n = 0;
                while n < weights_from_pigs[non_win_type_count].len() {
                    if let Some(index) =
                        win_dist_index_map.get(&F64Wrapper(wins_for_fences[non_win_type_count][n]))
                    {
                        weights[*index] += weights_from_pigs[non_win_type_count][n] / fence.hr;
                        // norm_factor +=  weights_from_ pigs[non_win_type_count][n]/fence.hr;
                    }
                    n += 1;
                }
                non_win_type_count += 1;
            }
        }

        score = run_simulation(
            &sorted_wins,
            &weights,
            test_spins[test_spins.len() - 1],
            trials,
            bet_amount,
            test_spins,
            &mut banks,
            test_spins_weights,
            pmb_rtp,
        );

        // RESET THE VALUES
        if score != 0.0 && score >= best_score {
            best_score = score;
            show_pigs.push(ShowPig {
                pig_indexes: pig_indexes,
                success_score: score,
            })
        }
    }
    show_pigs
}

fn sort_wins_by_parameter(
    fence: &mut Fence,
    force_options: &Vec<SearchResult>,
    lookup_table: &mut HashMap<u32, LookUpTableEntry>,
) {
    if fence.win_type {
        let identity_win = fence.identity_condition.win_range_start;
        let keys_to_remove: Vec<u32> = if fence.identity_condition.opposite {
            lookup_table
                .iter()
                .filter(|(_, result)| result.win != identity_win)
                .map(|(&k, _)| k)
                .collect()
        } else {
            lookup_table
                .iter()
                .filter(|(_, result)| result.win == identity_win)
                .map(|(&k, _)| k)
                .collect()
        };

        for key in keys_to_remove {
            let entry = lookup_table.remove(&key);
            if let Some(result) = entry {
                fence
                    .win_dist
                    .entry(F64Wrapper(result.win))
                    .or_insert(Vec::new())
                    .push(result.id);
            }
        }
    } else {
        let i_c = &mut fence.identity_condition;

        if i_c.search.is_empty() && i_c.win_range_start == -1.0 && i_c.opposite == false {
            for (book_id, entry) in lookup_table {
                fence
                    .win_dist
                    .entry(F64Wrapper(entry.win))
                    .or_insert(Vec::new())
                    .push(entry.id);
                // lookup_table.remove(book_id);
            }
        } else {
            for option in force_options {
                let mut condition_satisfied = true; // Start assuming the condition is satisfied
                for (_i, i_c_key) in i_c.search.iter().enumerate() {
                    if i_c_key.value != "None" {
                        // Retrieve the value from the HashMap based on the i_c_key which is the key
                        // Compare the retrieved value after converting it to a string
                        let search_key_exists = option.search.iter().any(|search_key| {
                            search_key.name == i_c_key.name && search_key.value == i_c_key.value
                        });
                        if !search_key_exists {
                            // If the key is not found in the HashMap, the condition is not satisfied
                            condition_satisfied = false;
                            break;
                        }
                    }
                }

                if i_c.opposite {
                    condition_satisfied = !condition_satisfied;
                }
                if condition_satisfied {
                    for book_id in &option.bookIds {
                        if lookup_table.contains_key(book_id) {
                            let entry = lookup_table.get(book_id).unwrap();
                            fence
                                .win_dist
                                .entry(F64Wrapper(entry.win))
                                .or_insert(Vec::new())
                                .push(entry.id);
                            lookup_table.remove(book_id);
                        }
                    }
                }
            }
        }
    }
}

fn parse_fence_info(
    fence: &FenceJson,
    total_prob: &mut f64,
    bet_amount: f64,
    json_dresses: &Vec<DressJson>,
) -> Fence {
    let name: String = fence.name.clone();
    // Need to get the Values from fence and convert them to floats.
    let mut avg_win = fence
        .avg_win
        .clone()
        .unwrap_or(String::from("-1"))
        .parse::<f64>()
        .unwrap();
    let hr_str = fence.hr.clone().unwrap_or(String::from("-1"));
    let mut hr: f64 = -1.0;

    if hr_str != String::from("x") {
        hr = fence
            .hr
            .clone()
            .unwrap_or(String::from("-1"))
            .parse::<f64>()
            .unwrap();
    }

    let mut rtp = fence
        .rtp
        .clone()
        .unwrap_or(String::from("-1"))
        .parse::<f64>()
        .unwrap();
    let identity_condition = fence.identity_condition.clone();

    if hr_str != "x" && (hr > 0.0) & (rtp > 0.0) {
        avg_win = hr * rtp;
    }
    if hr_str != "x" && (hr > 0.0) & (avg_win > 0.0) {
        rtp = avg_win / hr;
    }
    if hr_str != "x" && hr < 0.0 && (rtp > 0.0) & (avg_win > 0.0) {
        hr = avg_win / rtp / bet_amount
    }
    if hr > 0.0 {
        *total_prob += 1.0 / hr;
    }
    // println!("name: {},avg_win: {},hr: {},rtp: {},ic:{}",name,avg_win,hr,rtp,identity_condition) ;

    let mut wins: Vec<f64> = vec![];
    let mut win_type = false;

    // println!("{}",split_string.len());
    if identity_condition.win_range_start > -1.0
        && identity_condition.win_range_end == identity_condition.win_range_start
    {
        wins.push(identity_condition.win_range_end);
        win_type = true;
    }
    let mut dresses: Vec<Dress> = Vec::new();
    for json_dress in json_dresses {
        let fence = json_dress.fence.clone();
        if fence == name {
            let scaler_factor = parse_scale_factor(&json_dress.scale_factor);
            let identity_condition_win_range = json_dress
                .identity_condition_win_range
                .clone()
                .unwrap_or([0.0, 0.0]);
            let prob = json_dress.prob.clone().unwrap_or(1.0);
            dresses.push(Dress {
                fence: fence,
                scale_factor: scaler_factor,
                identity_condition_win_range: identity_condition_win_range,
                prob: prob,
            });
        }
    }

    let win_dist: HashMap<F64Wrapper, Vec<u32>> = HashMap::new();
    let min_mean_to_median = fence
        .min_mean_to_median
        .clone()
        .unwrap_or(String::from("0"))
        .parse::<f64>()
        .unwrap();

    let max_mean_to_median = fence
        .max_mean_to_median
        .clone()
        .unwrap_or(String::from("10"))
        .parse::<f64>()
        .unwrap();

    return Fence {
        name: name,
        hr: hr,
        rtp: rtp,
        avg_win: avg_win,
        identity_condition: identity_condition,
        win_type: win_type,
        dresses: dresses,
        wins: wins,
        win_dist: win_dist,
        opposite_statement: false,
        min_mean_to_median: min_mean_to_median,
        max_mean_to_median: max_mean_to_median,
    };
}
pub struct Dress {
    pub fence: String,
    pub scale_factor: ScaleFactor,
    pub identity_condition_win_range: [f64; 2],
    pub prob: f64,
}
pub struct Fence {
    pub name: String,
    pub hr: f64,
    pub rtp: f64,
    pub avg_win: f64,
    pub identity_condition: IdentityCondition,
    pub win_type: bool,
    pub dresses: Vec<Dress>,
    pub wins: Vec<f64>,
    pub win_dist: HashMap<F64Wrapper, Vec<u32>>,
    pub opposite_statement: bool,
    pub min_mean_to_median: f64,
    pub max_mean_to_median: f64,
}
pub struct PigHeaven<'a> {
    pub bet_amount: f64,
    pub wins: Vec<f64>,
    pub rtp: f64,
    pub pig_params: Vec<&'a mut Dress>,
    pub num_pigs: u32,
    pub max_win: f64,
    pub min_win: f64,
    pub avg_win: f64,
}
#[derive(Clone)]
pub struct Pig {
    pub amps: Vec<f64>,
    pub mus: Vec<f64>,
    pub stds: Vec<f64>,
    pub params: Vec<f64>,
    pub apply_parms: Vec<Vec<u16>>,
    pub rtp: f64,
    pub sum_dist: f64,
    pub random_seeds: Vec<u32>,
    pub random_weights: Vec<f64>,
    pub random_apply_params: Vec<Vec<usize>>,
}
pub enum ScaleFactor {
    Factor(f64),
    FactorR(f64),
}

fn create_ancestors(
    pig_heaven: &PigHeaven,
    min_mean_to_median: f64,
    max_mean_to_median: f64,
    bias_application: BiasJson,
    max_trial_dist: u32,
) -> Vec<Pig> {
    let mut pos_pigs: Vec<Pig> = Vec::with_capacity((pig_heaven.num_pigs as f64).sqrt() as usize);
    let mut neg_pigs: Vec<Pig> = Vec::with_capacity((pig_heaven.num_pigs as f64).sqrt() as usize);
    let mut extra_params: Vec<Dress> = Vec::with_capacity(2);
    println!("Creating Initial Random Distributions...");
    let mut go_back_down = false;
    let mut std_weight = 70.0;

    let mut rng = rand::thread_rng();

    let mut loop_count = 0;
    let mut amps: Vec<f64> = Vec::with_capacity(max_trial_dist as usize);
    let mut mus: Vec<f64> = Vec::with_capacity(max_trial_dist as usize);
    let mut stds: Vec<f64> = Vec::with_capacity(max_trial_dist as usize);
    let mut already_printed = false;
    let mut bool_added_extra_parms = false;

    while (pos_pigs.len() as f64) < (pig_heaven.num_pigs as f64).sqrt()
        || (neg_pigs.len() as f64) < (pig_heaven.num_pigs as f64).sqrt()
    {
        loop_count += 1;
        if !go_back_down {
            std_weight = f64::min(
                std_weight * (1.0 + 1.0 / (pig_heaven.num_pigs as f64).powf(0.9)),
                400.0,
            );
        } else {
            std_weight = f64::min(
                std_weight * (1.0 - 1.0 / (pig_heaven.num_pigs as f64).powf(0.9)),
                400.0,
            );
        }
        if (std_weight - 400.0).abs() < 0.00001 {
            go_back_down = true;
        }
        std_weight = f64::max(std_weight, 20.0);
        if (std_weight - 20.0).abs() < 0.00001 {
            go_back_down = false;
        }
        let variables: u32 = rng.gen_range(5..=max_trial_dist);
        amps.clear();
        mus.clear();
        stds.clear();

        if loop_count % 2 == 0 {
            for _ in 0..variables {
                amps.push(rng.gen_range(1..=14) as f64);
                let v = rng.gen::<f64>();
                if bias_application.prob > 0.0 && v <= bias_application.prob {
                    let m = rng.gen_range(bias_application.range[0]..=bias_application.range[1]);
                    mus.push(m);
                } else {
                    let condition = v % 2.0 == 0.0;
                    mus.push(
                        pig_heaven.avg_win
                            * ((v * 0.25 + 1.0) * condition as i32 as f64
                                + (1.0 - v * 0.25) * (!condition as i32 as f64))
                            * (rng.gen_range(5..=15) as f64 / 10.0),
                    );
                }
                stds.push(rng.gen::<f64>() * 30.0 * rng.gen::<f64>() * std_weight);
            }
        } else {
            for _ in 0..variables {
                let v = rng.gen::<f64>();
                let random_value2: f64 = rng.gen();
                if bias_application.prob > 0.0 && v <= bias_application.prob {
                    mus.push(rng.gen_range(bias_application.range[0]..=bias_application.range[1]));
                } else {
                    mus.push(f64::max(
                        v * pig_heaven.avg_win + 0.01 * random_value2 * pig_heaven.max_win,
                        pig_heaven.min_win,
                    ));
                }
                stds.push(rng.gen::<f64>() * std_weight);
                amps.push(rng.gen::<f64>());
            }
        }

        let mut params: Vec<f64> = Vec::new();
        let mut apply_parms: Vec<Vec<u16>> = Vec::new();
        let mut count = 0;

        for dress in &pig_heaven.pig_params {
            if rng.gen::<f64>() < dress.prob {
                let scale_factor = match dress.scale_factor {
                    ScaleFactor::Factor(factor) => factor,
                    ScaleFactor::FactorR(factor) => factor * rng.gen::<f64>(),
                };

                let param_list = dress.identity_condition_win_range.clone();
                params.extend(param_list);
                params.push(scale_factor);

                let indexes: Vec<u16> = (0..mus.len()).map(|i| i as u16).collect();
                apply_parms.insert(count, indexes);
                count += 1;
            }
        }
        for extra_dress in &extra_params {
            let scale_factor = match extra_dress.scale_factor {
                ScaleFactor::Factor(factor) => factor,
                ScaleFactor::FactorR(factor) => factor * rng.gen::<f64>(),
            };

            let param_list = extra_dress.identity_condition_win_range.clone();
            params.extend(param_list);
            params.push(scale_factor);

            let indexes: Vec<u16> = (0..mus.len()).map(|i| i as u16).collect();
            apply_parms.insert(count, indexes);
            count += 1;
        }

        let random_seed: Vec<u32> = vec![rng.gen_range(0..=1000000000) as u32];
        let random_weight: Vec<f64> = vec![rng.gen::<f64>()];
        let mut new_pig = Pig {
            amps: Vec::new(),
            mus: Vec::new(),
            stds: Vec::new(),
            params: Vec::new(),
            apply_parms: Vec::new(),
            // apply_parms: HashMap::new(),
            random_seeds: random_seed,
            random_weights: random_weight,
            random_apply_params: Vec::new(),
            rtp: 0.0,
            sum_dist: 0.0,
        };
        mem::swap(&mut new_pig.amps, &mut amps);
        mem::swap(&mut new_pig.mus, &mut mus);
        mem::swap(&mut new_pig.stds, &mut stds);
        mem::swap(&mut new_pig.params, &mut params);
        mem::swap(&mut new_pig.apply_parms, &mut apply_parms);

        let (rtp, sum_dist) = get_weights_no_weight_array(
            &pig_heaven.wins,
            &new_pig.amps,
            &new_pig.mus,
            &new_pig.stds,
            &new_pig.params,
            &new_pig.apply_parms,
            &new_pig.random_seeds,
            &new_pig.random_weights,
        );
        new_pig.rtp += rtp;
        new_pig.sum_dist += sum_dist;
        if new_pig.rtp > pig_heaven.avg_win
            && (pos_pigs.len() as f64) < (pig_heaven.num_pigs as f64).sqrt()
        {
            pos_pigs.push(new_pig);
        } else if new_pig.rtp < pig_heaven.avg_win
            && (neg_pigs.len() as f64) < (pig_heaven.num_pigs as f64).sqrt()
        {
            neg_pigs.push(new_pig);
        }

        if (pos_pigs.len() as f64) >= (pig_heaven.num_pigs as f64).sqrt() && !bool_added_extra_parms
        {
            bool_added_extra_parms = true;
            let dress = Dress {
                fence: "".to_string(),
                scale_factor: ScaleFactor::Factor(150.0), // Use the ScaleFactor enum variant Factor
                identity_condition_win_range: [pig_heaven.min_win, pig_heaven.avg_win / 2.0],
                prob: 1.0,
            };
            extra_params.push(dress);

            let dress2 = Dress {
                fence: "".to_string(),
                scale_factor: ScaleFactor::Factor(0.0001), // Use the ScaleFactor enum variant Factor
                identity_condition_win_range: [pig_heaven.avg_win / 2.0, pig_heaven.max_win],
                prob: 1.0,
            };
            extra_params.push(dress2);
        }

        if (neg_pigs.len() as f64) >= (pig_heaven.num_pigs as f64).sqrt() && !bool_added_extra_parms
        {
            bool_added_extra_parms = true;
            let dress = Dress {
                fence: "".to_string(),
                scale_factor: ScaleFactor::Factor(50.0),
                identity_condition_win_range: [pig_heaven.avg_win * 2.0, pig_heaven.max_win],
                prob: 1.0,
            };
            extra_params.push(dress);
            let dress2 = Dress {
                fence: "".to_string(),
                scale_factor: ScaleFactor::Factor(0.0001),
                identity_condition_win_range: [pig_heaven.min_win, pig_heaven.avg_win],
                prob: 1.0,
            };
            extra_params.push(dress2);
        }

        if loop_count > 5 * pig_heaven.num_pigs {
            if neg_pigs.len() > pos_pigs.len() {
                if !already_printed {
                    println!("RTP too low...");
                    already_printed = true;
                }
            } else {
                if !already_printed {
                    println!("RTP too high...");
                    already_printed = true;
                }
            }
        }
    }

    println!("Combining Criteria Distributions....");
    let mut pigs_for_fence: Vec<Pig> = Vec::new();
    let mut pig_count = 0;
    while pig_count < pos_pigs.len() * neg_pigs.len() {
        let mut pig_volatility_satisfied = false;
        let mut satisifed_count = 0;
        while !pig_volatility_satisfied {
            satisifed_count += 1;

            let pos_pig_index = rng.gen_range(0..=pos_pigs.len() - 1);
            let neg_pig_index = rng.gen_range(0..=neg_pigs.len() - 1);

            let pos_pig = &pos_pigs[pos_pig_index];
            let neg_pig = &neg_pigs[neg_pig_index];

            let pig = breed_pigs(pos_pig, neg_pig, &pig_heaven);
            let mut weights: Vec<f64> = vec![0.0; pig_heaven.wins.len()];
            let mut random_weights_to_apply: Vec<Vec<f64>> = Vec::new();
            random_weights_to_apply.push(vec![0.0; pig_heaven.wins.len()]);
            random_weights_to_apply.push(vec![0.0; pig_heaven.wins.len()]);
            get_weights(
                &pig_heaven.wins,
                &mut weights,
                &pig.amps,
                &pig.mus,
                &pig.stds,
                &pig.params,
                &pig.apply_parms,
                &pig.random_seeds,
                &pig.random_weights,
                &pig.random_apply_params,
                &mut random_weights_to_apply,
            );

            let mut sum_dist: f64 = 0.0;
            let mut median = 0.0;
            for win_index in 0..pig_heaven.wins.len() {
                sum_dist += weights[win_index];
                if sum_dist >= 0.5 {
                    median = pig_heaven.wins[win_index];
                    break;
                }
            }
            if !(median > 0.0
                && (pig_heaven.avg_win / median <= min_mean_to_median
                    || pig_heaven.avg_win / median >= max_mean_to_median))
            {
                pig_volatility_satisfied = true;
            }
            if satisifed_count % 500 == 0 {
                println!(
                    "Mean to Median {} {} {}",
                    pig_heaven.avg_win / median,
                    min_mean_to_median,
                    max_mean_to_median
                );
            }
            if pig_volatility_satisfied {
                pigs_for_fence.push(breed_pigs(pos_pig, neg_pig, &pig_heaven));
            }
        }
        pig_count += 1;
    }
    return pigs_for_fence;
}

fn get_weights_no_weight_array(
    wins: &Vec<f64>,
    amps: &Vec<f64>,
    mus: &Vec<f64>,
    stds: &Vec<f64>,
    params: &Vec<f64>,
    apply_parms: &[Vec<u16>],
    // apply_parms: &HashMap<u16, Vec<u16>>,
    random_seeds: &Vec<u32>,
    random_weights: &Vec<f64>,
) -> (f64, f64) {
    let rtp: f64;
    let mut sum_dist = 0.0;
    let mut total_win: f64 = 0.0;

    let mut random_weights_to_apply: Vec<Vec<f64>> = Vec::with_capacity(random_seeds.len());

    for index in 0..random_seeds.len() {
        random_weights_to_apply.push(vec![0.0; wins.len()]);
        let mut rng = StdRng::seed_from_u64(random_seeds[index] as u64);
        for array_index in 0..wins.len() {
            let random_num = rng.gen_range(-100..=100) as f64;
            random_weights_to_apply[index][array_index] =
                1.0 + ((random_num) / 100.0) * random_weights[index];
        }
    }

    for index in 0..wins.len() {
        let mut total_weight = 0.0;
        for norm_index in 0..amps.len() {
            let mut weight = amps[norm_index]
                * (1.0
                    + 20000.0
                        * (1.0 / ((stds[norm_index] * (2.0 * 3.14)).sqrt()))
                        * ((2.71_f64).powf(
                            -0.5 * ((wins[index] - mus[norm_index]) / stds[norm_index]).powf(2.0),
                        )));

            for param_index in 0..(params.len() / 3) {
                if let Some(apply_norm_indexes) = apply_parms.get(param_index) {
                    if apply_norm_indexes
                        .binary_search(&(norm_index as u16))
                        .is_ok()
                        && wins[index] >= params[3 * param_index]
                        && wins[index] <= params[3 * param_index + 1]
                    {
                        weight *= params[3 * param_index + 2];
                    }
                }
            }
            weight *= random_weights_to_apply[0][index];
            total_weight += weight
        }
        sum_dist += total_weight;
        total_win += total_weight * wins[index]
    }

    rtp = total_win / sum_dist;
    (rtp, sum_dist)
}

fn get_weights(
    wins: &Vec<f64>,
    weights: &mut Vec<f64>,
    amps: &Vec<f64>,
    mus: &Vec<f64>,
    stds: &Vec<f64>,
    params: &Vec<f64>,
    apply_parms: &Vec<Vec<u16>>,
    random_seeds: &Vec<u32>,
    random_weights: &Vec<f64>,
    random_apply_params: &Vec<Vec<usize>>,
    random_weights_to_apply: &mut Vec<Vec<f64>>,
) {
    for index in 0..random_seeds.len() {
        let mut rng = StdRng::seed_from_u64(random_seeds[index] as u64);
        for array_index in 0..wins.len() {
            let random_num = rng.gen_range(-100..=100) as f64;
            random_weights_to_apply[index][array_index] =
                1.0 + ((random_num) / 100.0) * random_weights[index];
        }
    }
    for index in 0..wins.len() {
        let mut total_weight = 0.0;
        for norm_index in 0..amps.len() {
            let mut weight = amps[norm_index]
                * (1.0
                    + 20000.0
                        * (1.0 / ((stds[norm_index] * (2.0 * 3.14)).sqrt()))
                        * ((2.71_f64).powf(
                            -0.5 * ((wins[index] - mus[norm_index]) / stds[norm_index]).powf(2.0),
                        )));

            for param_index in 0..(params.len() / 3) {
                if let Some(apply_norm_indexes) = apply_parms.get(param_index) {
                    if apply_norm_indexes
                        .binary_search(&(norm_index as u16))
                        .is_ok()
                        && wins[index] >= params[3 * param_index]
                        && wins[index] <= params[3 * param_index + 1]
                    {
                        weight *= params[3 * param_index + 2];
                    }
                }
            }
            for rand_index in 0..random_apply_params.len() {
                if random_apply_params[rand_index].contains(&norm_index) {
                    weight *= random_weights_to_apply[rand_index][index];
                }
            }
            total_weight += weight;
        }

        weights[index] = total_weight;
    }
    // let mut rtp = 0.0;
    // for index in 0..wins.len(){
    //     rtp += wins[index]*weights[index]
    // }
    // print!("{}",rtp)
}

fn breed_pigs(pos_pig: &Pig, neg_pig: &Pig, pig_heaven: &PigHeaven) -> Pig {
    let mut added_params = 0;
    let mut new_pig_parms: Vec<f64> = Vec::new();
    let mut new_pig_apply_parms: Vec<Vec<u16>> = Vec::new();

    for param_index in 0..(pos_pig.params.len() / 3) {
        new_pig_parms.extend(Vec::from([
            pos_pig.params.get(3 * param_index).expect("error"),
            pos_pig.params.get(3 * param_index + 1).expect("error"),
            pos_pig.params.get(3 * param_index + 2).expect("error"),
        ]));
        new_pig_apply_parms.insert(
            added_params.clone(),
            (0..pos_pig.mus.len()).map(|i| i as u16).collect(),
        );
        added_params += 1;
    }
    for param_index in 0..(neg_pig.params.len() / 3) {
        new_pig_parms.extend(Vec::from([
            neg_pig.params.get(3 * param_index).expect("error"),
            neg_pig.params.get(3 * param_index + 1).expect("error"),
            neg_pig.params.get(3 * param_index + 2).expect("error"),
        ]));
        new_pig_apply_parms.insert(
            added_params.clone(),
            (pos_pig.mus.len()..(pos_pig.mus.len() + neg_pig.mus.len()))
                .map(|i| i as u16)
                .collect(),
        );
        added_params += 1;
    }

    let (
        rtp,
        sum_dist,
        new_amps,
        new_stds,
        new_mus,
        new_random_seeds,
        new_random_weights,
        new_random_apply_params,
    ) = combine_distributions(pos_pig, neg_pig, pig_heaven);

    return Pig {
        amps: new_amps,
        mus: new_mus,
        stds: new_stds,
        params: new_pig_parms,
        apply_parms: new_pig_apply_parms,
        rtp,
        sum_dist: sum_dist,
        random_seeds: new_random_seeds,
        random_weights: new_random_weights,
        random_apply_params: new_random_apply_params,
    };
}

fn combine_distributions(
    pos_pig: &Pig,
    neg_pig: &Pig,
    pig_heaven: &PigHeaven,
) -> (
    f64,
    f64,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
    Vec<u32>,
    Vec<f64>,
    Vec<Vec<usize>>,
) {
    // @Rob these vectors could probably be declared before hand
    let weight = (pig_heaven.avg_win - neg_pig.rtp) / (pos_pig.rtp - neg_pig.rtp);
    let mut new_amps: Vec<f64> = Vec::new();
    let mut new_stds: Vec<f64> = Vec::new();
    let mut new_mus: Vec<f64> = Vec::new();

    new_amps.extend(
        pos_pig
            .amps
            .iter()
            .map(|amp| amp * weight / pos_pig.sum_dist),
    );
    new_amps.extend(
        neg_pig
            .amps
            .iter()
            .map(|amp| amp * (1.0 - weight) / neg_pig.sum_dist),
    );

    new_stds.extend(&pos_pig.stds);
    new_stds.extend(&neg_pig.stds);

    new_mus.extend(&pos_pig.mus);
    new_mus.extend(&neg_pig.mus);

    let rtp = weight * pos_pig.rtp + (1.0 - weight) * neg_pig.rtp;

    let new_random_weights: Vec<f64> = vec![pos_pig.random_weights[0], neg_pig.random_weights[0]];
    let new_random_seeds: Vec<u32> = vec![pos_pig.random_seeds[0], neg_pig.random_seeds[0]];
    let new_random_apply_parms: Vec<Vec<usize>> = Vec::from([
        (0..pos_pig.amps.len()).collect(),
        (pos_pig.amps.len()..pos_pig.amps.len() + neg_pig.amps.len()).collect(),
    ]);

    (
        rtp,
        1.0,
        new_amps,
        new_stds,
        new_mus,
        new_random_seeds,
        new_random_weights,
        new_random_apply_parms,
    )
}

fn parse_scale_factor(scale_factor: &str) -> ScaleFactor {
    if scale_factor.ends_with('r') {
        let value_without_r: &str = scale_factor.trim_end_matches('r');
        if let Ok(factor) = value_without_r.parse::<f64>() {
            return ScaleFactor::FactorR(factor);
        }
    }

    if let Ok(factor) = scale_factor.parse::<f64>() {
        ScaleFactor::Factor(factor)
    } else {
        // You might want to handle the error case here, e.g., return a default value.
        // For simplicity, I'm returning ScaleFactor::Factor(1.0) as a default.
        ScaleFactor::Factor(1.0)
    }
}

fn run_simulation(
    wins: &Array1<f64>,
    weights: &Array1<f64>,
    spins: u32,
    trials: u32,
    bet: f64,
    test_spins: &Vec<u32>,
    banks: &mut Array1<f64>,
    test_spins_weights: &Vec<f64>,
    pmb_rtp: f64,
) -> f64 {
    let num_test_spins = test_spins.len();
    let mut success: Vec<f64> = vec![0.0; num_test_spins];

    let mut rng = thread_rng();
    let banks_slice = banks.as_slice_mut().unwrap();
    let weighted_index = WeightedIndex::new(weights).expect("Invalid weights");

    for trial in 0..trials {
        let chosen_wins_indices = (0..spins)
            .map(|_| weighted_index.sample(&mut rng))
            .collect::<Vec<usize>>();

        for (i, &index) in chosen_wins_indices.iter().enumerate() {
            banks_slice[(trial * spins + i as u32) as usize] = wins[index];
        }
    }
    for trial in 0..trials {
        for (spin_index, &test_spin) in test_spins.iter().enumerate() {
            let bank_slice = &banks.slice(s![
                (trial as usize) * (spins as usize)..(trial * spins + test_spin) as usize
            ]);
            let total_bank: f64 = bank_slice.iter().sum();
            if (total_bank / (test_spin as f64 * bet)) >= pmb_rtp {
                success[spin_index] += 1.0;
            }
        }
    }

    let mut final_score = 0.0;
    for i in 0..success.len() {
        final_score += success[i] / (trials as f64) * test_spins_weights[i];
    }

    final_score
}

fn run_enhanced_simulation(
    wins: &Array1<f64>,
    weights: &Array1<f64>,
    spins: usize,
    trials: usize,
    bet: f64,
    test_spins: &Vec<u32>,
    pmb_rtp: f64,
) -> Vec<f64> {
    let num_spins = test_spins[test_spins.len() - 1usize] as usize;
    let total_spin_trials = num_spins * trials;

    let success: Vec<f64> = (0..num_spins)
        .into_par_iter()
        .map(|spin_index| {
            let mut spin_success = 0.0;

            for _ in 0..trials {
                let mut rng = thread_rng();
                let mut banks: Array1<f64> = Array1::zeros(spins);
                let banks_slice = banks.as_slice_mut().unwrap();
                let weighted_index = WeightedIndex::new(weights).expect("Invalid weights");

                for i in 0..spins {
                    banks_slice[i] = wins[weighted_index.sample(&mut rng)];
                }

                let bank_slice = &banks.slice(s![..(spin_index + 1) as usize]);
                let total_bank: f64 = bank_slice.iter().sum();
                if (total_bank / ((spin_index + 1) as f64 * bet)) >= pmb_rtp {
                    spin_success += 1.0;
                }
            }

            spin_success
        })
        .collect();

    let total_trials = trials as f64;
    success.iter().map(|s| s / total_trials).collect()
}

#[derive(Copy)]
pub struct F64Wrapper(f64);

impl F64Wrapper {
    // Method to convert bits to an f64 value
    fn from_bits(bits: u64) -> f64 {
        f64::from_bits(bits)
    }
    fn new(val: f64) -> Self {
        F64Wrapper(val)
    }

    fn value(&self) -> f64 {
        self.0
    }
    fn copy(&self) -> F64Wrapper {
        F64Wrapper(self.0)
    }
}

impl PartialEq for F64Wrapper {
    fn eq(&self, other: &Self) -> bool {
        let diff = (self.0 - other.0).abs() < 0.00000000001;
        diff
    }
}

impl Eq for F64Wrapper {}

impl PartialOrd for F64Wrapper {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        self.0.partial_cmp(&other.0)
    }
}

impl Clone for F64Wrapper {
    fn clone(&self) -> F64Wrapper {
        F64Wrapper(self.0)
    }
}

impl Ord for F64Wrapper {
    fn cmp(&self, other: &Self) -> Ordering {
        self.partial_cmp(other).unwrap_or(Ordering::Equal)
    }
}

impl Hash for F64Wrapper {
    fn hash<H: Hasher>(&self, state: &mut H) {
        // Convert the f64 to a bit representation and hash it
        let bits: u64 = self.0.to_bits();
        bits.hash(state);
    }
}

struct ShowPig {
    pub pig_indexes: Vec<usize>,
    pub success_score: f64
}
