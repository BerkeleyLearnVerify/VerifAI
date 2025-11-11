import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

import os
import csv
import argparse
import numpy as np
import gymnasium as gym
from functools import partial
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from metadrive.envs import MetaDriveEnv
from IPython.display import Image, clear_output
from metadrive.utils.doc_utils import generate_gif
from metadrive.component.map.base_map import BaseMap
from stable_baselines3.common.utils import set_random_seed
from metadrive.component.map.pg_map import MapGenerateMethod
from stable_baselines3.common.vec_env.subproc_vec_env import SubprocVecEnv
from metadrive.utils.draw_top_down_map import draw_top_down_map
from train import make_env

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test policy in MetaDrive")
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
        required=True,
        help="Saved model zip")
    parser.add_argument(
        "--n",
        type=int,
        default=10,
        help="Number of test samples")
    parser.add_argument(
        "--scenario",
        type=str,
        default="XX",
        help="Scenario string")
    parser.add_argument(
        "--gif",
        action="store_true",
        help="Generate gifs"
    )
    args = parser.parse_args()

    # while True:
    #     env=make_env(scenario=args.scenario, monitor=False)
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
    env = make_env(scenario=scenario, monitor=False)

    model = PPO.load(args.model)

    all_traces = []
    trace_id = 0

    if not args.gif:
        csv_path = os.path.join(args.save_dir, "traces.csv")
        f = open(csv_path, "w", newline="")
        writer = csv.DictWriter(f, fieldnames=["trace_id", "step", "x", "y", "heading",
                                               "speed", "action", "reward", "label"])

    for ep in range(args.n):
        obs, _ = env.reset()

        initial_speed = np.random.uniform(low=70/3.6, high=80/3.6)
        initial_velocity = env.vehicle.lane.direction * initial_speed
        env.vehicle.set_velocity(initial_velocity)

        done = False
        total_reward = 0.0
        step = 0
        label = False

        print(f"\n=== Episode {ep+1}/{args.n} ===")
        while not done and step <= env.config.horizon:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, done, truncated, info = env.step(action)
            total_reward += reward
            label = not done or info.get("arrive_dest")

            if args.gif:
                env.render(
                    mode="topdown",
                    screen_record=True,
                    window=False
                )
            else:
                agent = env.agent
                pos = agent.position
                heading = agent.heading_theta
                vel = agent.speed

                row = {
                    "trace_id": trace_id,
                    "step": step,
                    "x": pos[0],
                    "y": pos[1],
                    "heading": heading,
                    "speed": vel,
                    "action": action.tolist() if hasattr(action, "tolist") else action,
                    "reward": reward,
                    "label" : label
                }

                writer.writerow(row)

            step += 1

        print(f"Label: {label}")
        print(f"Episode reward: {total_reward:.2f}")

        if args.gif:
            gif_path = os.path.join(args.save_dir, f"trace_{trace_id:03d}.gif")
            env.top_down_renderer.generate_gif(gif_path)
            print(f"Saved gif to {gif_path}")

        trace_id += 1

    if not args.gif:
        f.close()

    env.close()

