import os
import csv
import numpy as np
from metadrive.envs import MetaDriveEnv
from metadrive.policy.expert_policy import ExpertPolicy


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


def generate_traces(
    seed: int = 0,
    save_dir: str = "storage/run0",
    n: int = 50,
    scenario: str = "XX",
    gif: bool = False
):
    """
    Runs MetaDrive simulation using an expert policy and logs trajectory traces.

    Args:
        seed (int): Random seed for reproducibility.
        save_dir (str): Directory where traces or gifs will be saved.
        n (int): Number of test episodes to run.
        scenario (str or int): Scenario string or ID.
        gif (bool): If True, generate top-down gifs instead of CSV traces.
    """


    scenario_id = int(scenario) if str(scenario).isdigit() else scenario
    env = make_env(scenario=scenario_id, monitor=False)
    
    model = None

    all_traces = []
    trace_id = 0

    # Create save dir
    os.makedirs(save_dir, exist_ok=True)

    if not gif:
        csv_path = os.path.join(save_dir, scenario, "traces.csv")
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        f = open(csv_path, "w", newline="")
        
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "trace_id", "step", "x", "y", "heading",
                "speed", "action", "reward", "label"
            ]
        )
        writer.writeheader()

    for ep in range(n):
        obs, _ = env.reset()
        
        expert_policy = ExpertPolicy(env.agent)

        initial_speed = np.random.uniform(low=70/3.6, high=80/3.6)
        initial_velocity = env.agent.lane.direction * initial_speed
        env.agent.set_velocity(initial_velocity)

        done = False
        total_reward = 0.0
        step = 0
        label = False

        while not done and step <= env.config.horizon:
            action = expert_policy.act()
                
            obs, reward, done, truncated, info = env.step(action)
            total_reward += reward
            label = not done or info.get("arrive_dest")

            if gif:
                env.render(mode="topdown", screen_record=True, window=False)
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
                    "label": label
                }
                writer.writerow(row)

            step += 1

        if gif:
            gif_path = os.path.join(save_dir, f"trace_{trace_id:03d}.gif")
            env.top_down_renderer.generate_gif(gif_path)
            print(f"Saved gif to {gif_path}")

        trace_id += 1

    if not gif:
        f.close()

    env.close()
    return

