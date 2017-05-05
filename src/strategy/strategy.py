class Strategy:
    def __init__(self):
        self._name = type(self).__name__

    @property
    def name(self):
        try:
            return self._name
        except AttributeError:
            self._name = type(self).__name__
            return self._name

    @staticmethod
    def get_strategy(name, configs):
        if name == 'overreact':
            from strategy.strategy_overreact import OverReactStrategy
            return OverReactStrategy(configs.overreact.top_drop_pct,
                                     configs.overreact.target_recover_rate,
                                     configs.overreact.recover_days,
                                     configs.overreact.recover_success_rate,
                                     configs.overreact.max_allowed_fallback,
                                     configs.overreact.max_fallback_rate)
        # No strategy found
        return None
