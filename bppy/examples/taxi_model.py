import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import datetime

from gymnasium.wrappers import TimeLimit

from taxi_helper import *
# fixate the random seed
np.random.seed(0)
# Create the Taxi environment
#env = gym.make('Taxi-v3', render_mode="human")
env = gym.make('Taxi-v3')

# Define hyperparameters
learning_rate = 0.1
discount_factor = 0.99
exploration_prob = 1.0
exploration_decay = 0.99
min_exploration_prob = 0.1
num_episodes = 200
# mode = "train"
mode = "eval"
avoid_illegal_actions = True
# Define a simple neural network model using PyTorch
class QNetwork(nn.Module):
    def __init__(self, input_size, output_size):
        super(QNetwork, self).__init__()
        self.fc1 = nn.Linear(input_size, 32)
        self.fc2 = nn.Linear(32, output_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        return self.fc2(x)

def check_model():
    model = QNetwork(env.observation_space.n, env.action_space.n)
    env.reset()
    action = env.action_space.sample()
    next_state, reward, terminated, truncated, info = env.step(action)
    print(next_state, ",", type(next_state))
    test_input_tensor = torch.eye(env.observation_space.n)[next_state]
    q_values = model(test_input_tensor).detach().numpy()
    print(q_values)

# Create the Q-network
model = QNetwork(env.observation_space.n, env.action_space.n)
optimizer = optim.Adam(model.parameters(), lr=learning_rate)
criterion = nn.MSELoss()  # Create an instance of the MSELoss class

if mode == "train":

    print(f"episode\texploration_prob\ttotal_reward")
    # Training loop
    for episode in range(num_episodes):
        state, info = env.reset()
        total_reward = 0
        terminated = False
        # Set the maximum number of steps per episode
        max_steps_per_episode = 200
        while not terminated and max_steps_per_episode > 0:
            # Epsilon-greedy exploration strategy
            if np.random.rand() < exploration_prob:
                action = env.action_space.sample()  # Explore
            else:
                state_input_tensor = torch.eye(env.observation_space.n)[state]
                q_values = model(state_input_tensor).detach().numpy()
                action = np.argmax(q_values)  # Exploit

            next_state, reward, terminated, truncated, info = env.step(action)
            # Calculate target Q-value using Q-learning update equation
            next_state_input_tensor = torch.eye(env.observation_space.n)[next_state]
            target_q = reward + discount_factor * np.max(model(next_state_input_tensor).detach().numpy())

            # Get current Q-value prediction
            state_input_tensor = torch.eye(env.observation_space.n)[state] # state is a tuple
            current_q = model(state_input_tensor).detach().numpy()
            current_q[action] = target_q

            # Compute the loss and perform backpropagation
            loss = criterion(torch.tensor(current_q, dtype=torch.float32),
                             model(torch.eye(env.observation_space.n)[state]))
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            # Compute the total reward
            total_reward += reward
            state = next_state
            max_steps_per_episode -= 1
            # print(f"max_steps_per_episode = {max_steps_per_episode}")
        # Decay exploration probability
        exploration_prob = max(exploration_prob * exploration_decay, min_exploration_prob)
        print(f"{episode + 1}\t{exploration_prob}\t{total_reward}")

    # Save the trained model with current timestamp
    now = datetime.datetime.now()
    model_name = now.strftime("%H_%M_%d_%m_%Y") + "_taxi_model.pt"
    torch.save(model.state_dict(), model_name)
    print("saved model", model_name)
else: # Load the trained model
    model.load_state_dict(torch.load("09_43_27_08_2023_taxi_model.pt"))
    print("loaded model")
    # Evaluate the trained agent
    total_rewards = []
    action = None
    for _ in range(50):
        state, info = env.reset()
        total_reward = 0
        terminated = False
        num_of_attempts = 0
        while not terminated and num_of_attempts < 50:
            q_values = model(
                torch.eye(env.observation_space.n)[state]).detach().numpy()
            # find actionable q values using list comprehension
            if avoid_illegal_actions:
                actionable_q_values = []
                for i in range(len(q_values)):
                    if info["action_mask"][i] == 1:
                        print(f"q_values[{i}] = {q_values[i]}")
                        actionable_q_values.append(q_values[i])
                    else:
                        print(f"q_values[{i}] = {-np.inf}")
                        actionable_q_values.append(-np.inf)
                action = np.argmax(actionable_q_values)
            else:  # allow illegal actions
                action = np.argmax(q_values)
                # Possible solution - randomn selection of the action
            print(f"Eval attempt: {num_of_attempts}, current action:", action_to_word(action))
            next_state, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            state = next_state
            num_of_attempts += 1

        total_rewards.append(total_reward)

    print(f"Average reward over 100 evaluation episodes: {np.mean(total_rewards)}")

