# Fees

**URL:** https://docs.tryliquid.xyz/trading/trading/fees

---

Ask
Fees
In order to support the development of the app, Liquid charges fees to users. 
Hyperliquid
On spot assets, where you buy the underlying assets, Liquid charges no additional fees, i.e., it charges exactly what Hyperliquid charges. 
On perpetual futures, which represent directional exposure to the underlying assets, Liquid applies uniform 5 bps fees to both opening and closing trades through builder fees. 
What to know about Liquid fees:
Fees are based on your account’s rolling 14 day trading volume.
Fees are assessed at the end of each day (UTC).
Maker rebates are paid out continuously on each trade directly to your wallet.
Liquid uses separate fee schedules for perps and spot trading.
Perps and spot volume are counted together to determine your fee tier.
Spot volume counts double toward your fee tier:
(14 day perps volume) + 2 * (14 day spot volume) = (14 day weighted volume)
For the sake of completeness, we show the full fee calculation here. 
Base rate
Diamond
Platinum
Gold
Silver
Bronze
Wood
Tier
14 Day Weighted Volume ($)
Taker
Maker
Taker
Maker
Taker
Maker
Taker
Maker
Taker
Maker
Taker
Maker
Taker
Maker
0
0.095%
0.065%
0.0770%
0.0590%
0.0815%
0.0605%
0.0860%
0.0620%
0.0883%
0.0628%
0.0905%
0.0635%
0.0928%
0.0643%
1
> 5M
0.090%
0.062%
0.0740%
0.0572%
0.0780%
0.0584%
0.0820%
0.0596%
0.0840%
0.0602%
0.0860%
0.0608%
0.0880%
0.0614%
2
> 25M
0.085%
0.058%
0.0710%
0.0548%
0.0745%
0.0556%
0.0780%
0.0564%
0.0798%
0.0568%
0.0815%
0.0572%
0.0833%
0.0576%
3
> 100M
0.080%
0.054%
0.0680%
0.0524%
0.0710%
0.0528%
0.0740%
0.0532%
0.0755%
0.0534%
0.0770%
0.0536%
0.0785%
0.0538%
4
> 500M
0.078%
0.050%
0.0668%
0.0500%
0.0696%
0.0500%
0.0724%
0.0500%
0.0738%
0.0500%
0.0752%
0.0500%
0.0766%
0.0500%
5
> 2B
0.076%
0.050%
0.0656%
0.0500%
0.0682%
0.0500%
0.0708%
0.0500%
0.0721%
0.0500%
0.0734%
0.0500%
0.0747%
0.0500%
6
> 7B
0.074%
0.050%
0.0644%
0.0500%
0.0668%
0.0500%
0.0692%
0.0500%
0.0704%
0.0500%
0.0716%
0.0500%
0.0728%
0.0500%
The table below shows spot fee tiers for Liquid traders.
Spot
14 Day Weighted Volume ($)
Base Taker
Base Maker
Diamond Taker
Diamond Maker
Platinum Taker
Platinum Maker
Gold Taker
Gold Maker
Silver Taker
Silver Maker
Bronze Taker
Bronze Maker
Wood Taker
Wood Maker
0
0.070%
0.040%
0.0420%
0.0240%
0.0490%
0.0280%
0.0560%
0.0320%
0.0595%
0.0340%
0.0630%
0.0360%
0.0665%
0.0380%
1
> 5M
0.060%
0.030%
0.0360%
0.0180%
0.0420%
0.0210%
0.0480%
0.0240%
0.0510%
0.0255%
0.0540%
0.0270%
0.0570%
0.0285%
2
> 25M
0.050%
0.020%
0.0300%
0.0120%
0.0350%
0.0140%
0.0400%
0.0160%
0.0425%
0.0170%
0.0450%
0.0180%
0.0475%
0.0190%
3
> 100M
0.040%
0.010%
0.0240%
0.0060%
0.0280%
0.0070%
0.0320%
0.0080%
0.0340%
0.0085%
0.0360%
0.0090%
0.0380%
0.0095%
4
> 500M
0.035%
0.000%
0.0210%
0.0000%
0.0245%
0.0000%
0.0280%
0.0000%
0.0298%
0.0000%
0.0315%
0.0000%
0.0333%
0.0000%
5
> 2B
0.030%
0.000%
0.0180%
0.0000%
0.0210%
0.0000%
0.0240%
0.0000%
0.0255%
0.0000%
0.0270%
0.0000%
0.0285%
0.0000%
6
> 7B
0.025%
0.000%
0.0150%
0.0000%
0.0175%
0.0000%
0.0200%
0.0000%
0.0213%
0.0000%
0.0225%
0.0000%
0.0238%
0.0000%
Ostium
On Ostium assets, fees are charged only when entering a position, unlike in Hyperliquid where they are charged when exiting a position as well. Thus, 10 bps of taker fees on Ostium is equivalent to 5 bps of taker fees on Hyperliquid, excluding liquidations. 
Ostium's fees on entry / exit are: 
Crypto: 
Maker / Taker: 3bps / 10bps
On Ostium, maker fees apply only if the leverage is at most 20x and if the trade reduces the OI imbalance. Otherwise, taker fees apply. 
Indices
All trades are taker; and the fees are 5 bps. 
FX
All trades are taker, the fees are 3 bps except for USD/MXN, which is 5 bps. 
Stocks
All trades are taker, the fees are 5 bps. 
Commodities
All trades are taker, and the fees vary by asset:
Pair Name
Taker fees
XAU / USD
3 bps
CL / USD
10 bps
HG / USD
15 bps
XAG / USD
15 bps
XPT / USD
20 bps
XPD / USD
20 bps
On all Ostium trades, Liquid takes an additional 5 bps. 
Previous
Trading
Next
TP / SL
Last updated 9 days ago

## 📝 Code Examples

### Example 1

```
(14 day perps volume) + 2 * (14 day spot volume) = (14 day weighted volume)
```

## 🖼️ Images

### Image 1
**Local path:** `liquid_images/732954278814.png`
**Source:** https://docs.tryliquid.xyz/~gitbook/image?url=https%3A%2F%2F3619730017-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Forganizations%252F7hIYFerB5CRhj4HAzMfR%252Fsites%252Fsite_vj9qa%252Ficon%252FGWUh1d6uaEQ0Bw9TIQ4S%252FIcon.jpg%3Falt%3Dmedia%26token%3D91884328-081d-40cb-94ff-c264be1e3241&width=32&dpr=4&quality=100&sign=e30c0be8&sv=2

### Image 2
**Local path:** `liquid_images/732954278814.png`
**Source:** https://docs.tryliquid.xyz/~gitbook/image?url=https%3A%2F%2F3619730017-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Forganizations%252F7hIYFerB5CRhj4HAzMfR%252Fsites%252Fsite_vj9qa%252Ficon%252FGWUh1d6uaEQ0Bw9TIQ4S%252FIcon.jpg%3Falt%3Dmedia%26token%3D91884328-081d-40cb-94ff-c264be1e3241&width=32&dpr=4&quality=100&sign=e30c0be8&sv=2

