import logging
import random

from src.envs.tower_env import TowerEnv
from src.agents.q_agent import QLearningAgent
from src.agents.telemetry import (
    TrainingConfig,
    TrainingTelemetryRecorder,
    build_step_event,
)
from src.core.game import RECORD_DIR


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

NUM_DISCS = 5
MAX_STEPS = 150
MAX_EPISODES = 1000
SEED = 7
TELEMETRY_FILENAME = "qlearningagent_training.json"


def train(
    output_path=None,
    *,
    num_discs: int = NUM_DISCS,
    max_steps: int = MAX_STEPS,
    max_episodes: int = MAX_EPISODES,
    seed: int | None = SEED,
    log_every: int = 25,
):
    optimal_steps = 2**num_discs - 1
    env = TowerEnv(num_discs=num_discs, max_steps=max_steps)
    agent = QLearningAgent(
        action_size=6,
        alpha=0.1,
        gamma=0.99,
        epsilon=1.0,
        epsilon_decay=0.995,
        min_epsilon=0.01,
        rng=random.Random(seed),
    )
    config = TrainingConfig(
        num_discs=num_discs,
        max_steps=max_steps,
        max_episodes=max_episodes,
        optimal_steps=optimal_steps,
        alpha=agent.alpha,
        gamma=agent.gamma,
        epsilon=agent.epsilon,
        epsilon_decay=agent.epsilon_decay,
        min_epsilon=agent.min_epsilon,
        seed=seed,
    )
    recorder = TrainingTelemetryRecorder(config=config)
    output_path = output_path or RECORD_DIR / TELEMETRY_FILENAME

    for ep in range(max_episodes):
        obs, _ = env.reset()
        total_reward = 0
        done = False
        terminated = False
        truncated = False
        epsilon_start = agent.epsilon
        episode_steps = []

        while not done:
            decision = agent.select_action(obs)
            source_rod_idx, target_rod_idx = env.action_map[decision.action]
            next_obs, reward, terminated, truncated, _ = env.step(decision.action)

            agent.learn(obs, decision.action, reward, next_obs, terminated, truncated)
            q_values_after = agent.get_q_values(tuple(obs["observation"]))
            episode_steps.append(build_step_event(
                step_index=len(episode_steps),
                obs=obs,
                decision=decision,
                source_rod_idx=source_rod_idx,
                target_rod_idx=target_rod_idx,
                disc_id=env.current_move_event.disc_id,
                reward=reward,
                next_obs=next_obs,
                terminated=terminated,
                truncated=truncated,
                q_values_after=q_values_after,
            ))

            obs = next_obs
            total_reward += reward
            done = terminated or truncated

        agent.decay_epsilon()
        recorder.record_episode(
            episode_index=ep,
            epsilon_start=epsilon_start,
            epsilon_end=agent.epsilon,
            total_reward=total_reward,
            steps=episode_steps,
            terminated=terminated,
            truncated=truncated,
            q_table=agent.q_table,
        )

        is_optimal = terminated and len(episode_steps) == optimal_steps
        should_log = ep == 0 or (ep + 1) % log_every == 0 or is_optimal
        if should_log:
            logger.info(
                "Episode %s | Reward: %s | Steps: %s | Epsilon: %.2f",
                ep + 1,
                total_reward,
                len(episode_steps),
                agent.epsilon,
            )

        if is_optimal:
            logger.info("Stopping at first optimal solve on episode %s.", ep + 1)
            break

    saved_path = recorder.save(output_path)
    logger.info("Saved training telemetry to %s.", saved_path)
    return saved_path


if __name__ == "__main__":
    train()
