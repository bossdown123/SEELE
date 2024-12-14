from rest_framework import serializers
from .models import Order, TakeProfit, StopLoss
from alpaca.trading.enums import (
    OrderType,
    OrderSide,
    TimeInForce,
    OrderClass,
    PositionIntent,
)


class TakeProfitSerializer(serializers.ModelSerializer):
    class Meta:
        model = TakeProfit
        fields = ['limit_price']


class StopLossSerializer(serializers.ModelSerializer):
    class Meta:
        model = StopLoss
        fields = ['stop_price', 'limit_price']

class OrderSerializer(serializers.ModelSerializer):
    take_profit = TakeProfitSerializer(required=False, allow_null=True)
    stop_loss = StopLossSerializer(required=False, allow_null=True) 
    
    
    class Meta:
        model = Order
        fields = [
            'asset_id',
            'symbol',
            'notional',
            'qty',
            'order_type',
            'side',
            'time_in_force',
            'extended_hours',
            'client_order_id',
            'order_class',
            'take_profit',
            'stop_loss',
            'position_intent',
        ]

    