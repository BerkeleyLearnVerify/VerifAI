import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

import os
import argparse
import gymnasium as gym
from functools import partial
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from metadrive.envs import MetaDriveEnv
from IPython.display import Image, clear_output
from metadrive.utils.doc_utils import generate_gif
from metadrive.component.map.base_map import BaseMap
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import set_random_seed
from metadrive.component.map.pg_map import MapGenerateMethod
from stable_baselines3.common.vec_env.subproc_vec_env import SubprocVecEnv
from metadrive.utils.draw_top_down_map import draw_top_down_map


def make_env(scenario, monitor=False):
    config = MetaDriveEnv.default_config()
    config.map = scenario
    config.discrete_action=False
    config.horizon=2000
    config.num_scenarios=1000
    config.start_seed=1000
    config.traffic_density=0.05
    config.need_inverse_traffic=True
    config.accident_prob=0.0
    config.random_lane_width=False
    config.random_agent_model=False
    config.random_lane_num=False
    if monitor:
        return Monitor(MetaDriveEnv(config))
    else:
        return MetaDriveEnv(config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train policy in MetaDrive")
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility")
    parser.add_argument(
        "--save-dir",
        type=str,
        default="storage",
        help="Directory to save the trained model")
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model zip name"
    )
    parser.add_argument(
        "--n-envs",
        type=int,
        default=16,
        help="Number of parallel environments")
    parser.add_argument(
        "--timesteps",
        type=int,
        default=1_000_000,
        help="Number of environment steps")
    parser.add_argument(
        "--scenario",
        type=str,
        default="2",
        help="Scenario string")
    args = parser.parse_args()

    # while True:
    #     env=make_env(monitor=False)
    #     env.reset()
    #     ret = draw_top_down_map(env.current_map)
    #     # ret = env.render(mode="topdown", window=False)
    #     # ret = env.render(mode="topdown",
    #     #                  window=False,
    #     #                  # screen_size=(600, 600),
    #     #                  # camera_position=(50, 50)
    #     #                  )
    #     env.close()
    #     plt.axis("off")
    #     plt.imshow(ret)
    #     plt.show()
    #     clear_output()

    set_random_seed(args.seed)

    scenario = int(args.scenario) if args.scenario.isdigit() else args.scenario
    env = SubprocVecEnv([partial(make_env, scenario, True) for _ in range(args.n_envs)])

    model = PPO("MlpPolicy", env=env, n_steps=4096, verbose=1)
    model.learn(total_timesteps=args.timesteps, log_interval=1)
    env.close()
    clear_output()

    if args.model is None:
        arg_str = "_".join(f"{k}={v}" for k, v in vars(args).items() if k != "model")
        safe_arg_str = arg_str.replace("/", "_").replace(" ", "_")
        args.model = os.path.join(args.save_dir, f"model_{safe_arg_str}.zip")

    model.save(args.model)
    print("Training is finished.")

