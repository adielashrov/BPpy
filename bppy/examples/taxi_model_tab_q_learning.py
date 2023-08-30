import gymnasium as gym
import numpy as np
import datetime

# fixate the random seed
np.random.seed(0)
# Create the Taxi environment
# env = gym.make('Taxi-v3', render_mode="human")
env = gym.make('Taxi-v3')

# Initialize Q-values table with zeros
num_states = env.observation_space.n
num_actions = env.action_space.n
q_table = np.zeros((num_states, num_actions))

# Q-learning parameters
learning_rate = 0.1
discount_factor = 0.99
exploration_prob = 1.0
exploration_decay = 0.995
min_exploration_prob = 0.01
num_episodes = 5000
# mode = "train"
mode = "eval"
avoid_illegal_actions = True

if mode == "train":
    print(f"episode\ttotal_reward")
    # Training loop
    for episode in range(num_episodes):
        state, info = env.reset()
        total_reward = 0
        terminated = False
        # Set the maximum number of steps per episode
        max_steps_per_episode = 200
        while not terminated:
            # Epsilon-greedy exploration strategy
            if np.random.rand() < exploration_prob:
                action = env.action_space.sample()  # Explore
            else:
                action = np.argmax(q_table[state])  # Exploit

            next_state, reward, terminated, truncated, info = env.step(action)

            # Q-value update using Q-learning equation
            q_value = q_table[state][action]
            next_max_q = np.max(q_table[next_state])
            new_q_value = q_value + learning_rate * (reward + discount_factor * next_max_q - q_value)
            q_table[state][action] = new_q_value
            # Compute the total reward
            total_reward += reward
            state = next_state
            max_steps_per_episode -= 1
        # Decay exploration probability
        exploration_prob = max(exploration_prob * exploration_decay, min_exploration_prob)
        print(f"{episode + 1}\t{total_reward}")

    # Save the trained model with current timestamp
    now = datetime.datetime.now()
    q_table_name = now.strftime("%H_%M_%d_%m_%Y") + "_q_table"
    # Save the Q-table to a file using pickle
    np.save(q_table_name, q_table)
    print(f"saved q-table:{q_table_name}")
else: # evaluation
    # Load the Q-table from the file
    q_table = np.load('11_31_29_08_2023_q_table.npy')
    # Evaluate the trained Q-table
    num_evaluation_episodes = 100
    total_evaluation_reward = 0
    env = gym.make('Taxi-v3', render_mode="human")

    for _ in range(num_evaluation_episodes):
        state, info = env.reset()
        terminated = False

        while not terminated:
            action = np.argmax(q_table[state])
            next_state, reward, terminated, truncated, info = env.step(action)
            total_evaluation_reward += reward
            state = next_state

    average_evaluation_reward = total_evaluation_reward / num_evaluation_episodes
    print(f"Average evaluation reward: {average_evaluation_reward}")
