from src.envs.tower_env import TowerEnv
from src.agents.q_agent import QLearningAgent

def train():
    env = TowerEnv(num_discs=5, max_steps=150)
    agent = QLearningAgent(
        action_size=6, 
        alpha=0.1, 
        gamma=0.99, 
        epsilon=1.0, 
        epsilon_decay=0.995, 
        min_epsilon=0.01
    )
    episodes = 1000

    for ep in range(episodes):
        obs, _ = env.reset()
        total_reward = 0
        done = False

        while not done:
            action = agent.choose_action(obs)
            next_obs, reward, terminated, truncated, _ = env.step(action)
            agent.learn(obs, action, reward, next_obs, terminated, truncated)

            obs = next_obs
            total_reward += reward
            done = terminated or truncated
        
        agent.decay_epsilon()

        if (ep + 1) % 10 == 0:
            print(f"Epsiode {ep+1} | Reward: {total_reward} | Epsilon: {agent.epsilon:.2f}")


if __name__ == "__main__":
    train()