from django.db import models
from alpaca.common.models import UUID
from alpaca.trading.enums import (
    OrderType,
    OrderSide,
    TimeInForce,
    OrderClass,
    PositionIntent,
)
from alpaca.trading.requests import TakeProfitRequest, StopLossRequest
from django.core.exceptions import ValidationError

class TakeProfit(models.Model):
    limit_price = models.FloatField()

    def to_alpaca(self):
        return TakeProfitRequest(limit_price=self.limit_price)


class StopLoss(models.Model):
    stop_price = models.FloatField()
    limit_price = models.FloatField(null=True, blank=True)

    def to_alpaca(self):
        return StopLossRequest(stop_price=self.stop_price, limit_price=self.limit_price)


class Order(models.Model):
    asset_id = models.CharField(max_length=255, null=True, blank=True)
    symbol = models.CharField(max_length=255, null=True, blank=True)
    notional = models.FloatField(null=True, blank=True)
    qty = models.FloatField(null=True, blank=True)
    order_type = models.CharField(max_length=255, choices=[(i,i) for i in [
        OrderType.MARKET.value,
        OrderType.LIMIT.value,
        OrderType.STOP.value,
        OrderType.STOP_LIMIT.value,
        OrderType.TRAILING_STOP.value,
    ]], null=True, blank=True)
    side = models.CharField(max_length=255, choices=[(i,i) for i in [
        OrderSide.BUY.value,
        OrderSide.SELL.value
    ]], null=True, blank=True)
    time_in_force = models.CharField(max_length=255, choices=[(i,i) for i in [
        TimeInForce.GTC.value,
        TimeInForce.DAY.value,
        TimeInForce.OPG.value,
        TimeInForce.CLS.value,
        TimeInForce.IOC.value,
        TimeInForce.FOK.value
    ]], null=True, blank=True)
    extended_hours = models.BooleanField(null=True, blank=True)
    client_order_id = models.CharField(max_length=255, null=True, blank=True)
    order_class = models.CharField(max_length=255, choices=[(i,i) for i in [
        OrderClass.BRACKET.value,
        OrderClass.OCO.value,
        OrderClass.OTO.value,
        OrderClass.SIMPLE.value
    ]], null=True, blank=True)
    take_profit = models.OneToOneField(TakeProfit, on_delete=models.CASCADE, null=True, blank=True)
    stop_loss = models.OneToOneField(StopLoss, on_delete=models.CASCADE, null=True, blank=True)
    position_intent = models.CharField(max_length=255, choices=[(i,i) for i in [
        PositionIntent.BUY_TO_CLOSE.value,
        PositionIntent.BUY_TO_OPEN.value,
        PositionIntent.SELL_TO_CLOSE.value,
        PositionIntent.SELL_TO_OPEN.value
    ]], null=True, blank=True)

    def clean(self):
        # Validation logic to ensure either qty or notional is set
        if self.qty is None and self.notional is None:
            raise ValidationError("At least one of qty or notional must be provided.")
        elif self.qty is not None and self.notional is not None:
            raise ValidationError("Both qty and notional cannot be set.")
        
        if self.symbol is None and self.asset_id is None:
            raise ValidationError("Either symbol or asset_id must be provided")
        elif self.symbol is not None and self.asset_id is not None:
            raise ValidationError("Both symbol and asset_id cannot be set")

    def to_alpaca(self):
        return OrderRequest(
            symbol=self.symbol,
            qty=self.qty,
            notional=self.notional,
            side=OrderSide(self.side),
            type=OrderType(self.order_type),
            time_in_force=TimeInForce(self.time_in_force),
            extended_hours=self.extended_hours,
            client_order_id=self.client_order_id,
            order_class=OrderClass(self.order_class) if self.order_class else None,
            take_profit=self.take_profit.to_alpaca() if self.take_profit else None,
            stop_loss=self.stop_loss.to_alpaca() if self.stop_loss else None,
            position_intent=PositionIntent(self.position_intent) if self.position_intent else None,
        )
