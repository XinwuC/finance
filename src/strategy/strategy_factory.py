from strategy.strategy_overreact import OverReactStrategy


class StrategyFactory:
    @staticmethod
    def get_strategy(name, configs):
        if name == 'overreact':
            return OverReactStrategy(configs.overreact.top_drop_pct,
                                     configs.overreact.target_recover_rate,
                                     configs.overreact.recover_days,
                                     configs.overreact.recover_success_rate,
                                     configs.overreact.max_allowed_fallback,
                                     configs.overreact.max_fallback_rate)

        # No strategy found
        return None
