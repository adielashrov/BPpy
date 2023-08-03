from gymnasium.spaces import MultiDiscrete


class BPObservationSpace(MultiDiscrete):
    """

    """
    @property
    def np_random(self):
        return super().np_random

    @property
    def shape(self):
        return super().shape

    def sample(self):
        pass

    def seed(self, seed=None):
        return super().seed(seed)

    def contains(self, x):
        pass

    def __contains__(self, x):
        return super().__contains__(x)

    def __setstate__(self, state):
        super().__setstate__(state)

    def to_jsonable(self, sample_n):
        return super().to_jsonable(sample_n)

    def from_jsonable(self, sample_n):
        return super().from_jsonable(sample_n)

    def bp_state_to_gym_space(self, bthreads_states):
        raise NotImplementedError("bp_state_to_gym_space not implemented")