import logging

from src.envs.tower_env import TowerEnv
from src.agents.q_agent import QLearningAgent
from src.core.game import GameHistoryRecorder


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def train():
    env = TowerEnv(num_discs=5, max_steps=150)
    recorder = GameHistoryRecorder()
    agent = QLearningAgent(
        action_size=6,
        alpha=0.1,
        gamma=0.99,
        epsilon=1.0,
        epsilon_decay=0.995,
        min_epsilon=0.01
    )
    agent_class_name = agent.__class__.__name__.lower()
    episodes = 1000

    for ep in range(episodes):
        is_checkpoint_ep = (ep + 1) % 200 == 0
        obs, _ = env.reset()
        total_reward = 0
        done = False

        while not done:
            action = agent.choose_action(obs)
            next_obs, reward, terminated, truncated, _ = env.step(action)

            # Record the agent's action and new game state
            if is_checkpoint_ep:
                recorder.record_history(
                    disc_id=env.current_move_event.disc_id,
                    source_rod_idx=env.current_move_event.source_rod_idx,
                    target_rod_idx=env.current_move_event.target_rod_idx,
                    new_state=next_obs["observation"]
                )

            agent.learn(obs, action, reward, next_obs, terminated, truncated)

            obs = next_obs
            total_reward += reward
            done = terminated or truncated

        agent.decay_epsilon()

        if is_checkpoint_ep:
            recorder.set_json_filepath(f"{agent_class_name}_{ep}.json")
            recorder.save_to_file()
            recorder.reset()

            logger.info(f"Epsiode {ep+1} | Reward: {total_reward} | Epsilon: {agent.epsilon:.2f}")


if __name__ == "__main__":
    train()