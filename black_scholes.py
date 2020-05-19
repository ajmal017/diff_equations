import requests
import json
from scipy import stats
import math
from copy import deepcopy
import matplotlib.pyplot as plt
from collections import namedtuple
# import yfinance as yf


# to comfortably pack our data
Data = namedtuple('Data', 'spot strike time volatility rate mode ask bid dt')


API_URL = r"https://eodhistoricaldata.com/api/options/{}"
SHARE_NAME = r"AAPL.US"
API_TOKEN = r"OeAFFmMliFG5orCUuwAKQ8l4WWFQ67YX"


def calculate_k_arg(ask, bid):
    """
      this fucntion calculates the k argument
      which is used in Lelland's model
    """
    k = 2 * (ask - bid) / (ask + bid)
    return k


def calculate_volatility(v, k, delta):
    """
      this function calculates the improved volatility
      which is used in Lelland's model
    """
    new_v = math.sqrt(math.pow(v, 2) * (1 + math.sqrt(2 / math.pi) *
                                        (k / v) * math.sqrt(delta)))
    return new_v


def black_scholes(spot, strike, time, v, rf, cp):
    """
      returns price of either call or put option
      description of arguments:
      spot - current price of security (stock price in our case )
      strike - strike price
      t - expiration time
      v - volatility
      rf : risk-free rate
      cp : +1/-1 for call/put
    """
    # get normal value of time денис напиши нормально
    t = time / 365
    # calculate d_1 and d_2 arguments for black_scholes
    d1 = (math.log(spot / strike) + (rf + 0.5 * math.pow(v, 2)) * t) / (
            v * math.sqrt(t))
    d2 = d1 - v * math.sqrt(t)

    # and finally calculate black scholes option price with black scholes formula
    optprice = cp * spot * stats.norm.cdf(cp * d1) - cp * strike * \
               math.exp(-rf * t) * stats.norm.cdf(cp * d2)
    return optprice


def black_scholes_from_scratch(data):
    return black_scholes(data['spot'],
                         data['strike'],
                         data['t'],
                         data['v'],
                         data['rf'],
                         data['cp'])


def extract_spot(response):
    return response.get("lastTradePrice")


def get_raw_data(api_url, share_name, token):
    payload = {"api_token" : token}
    response = requests.get(
                            api_url.format(share_name),
                            params=payload
                            )
    return response.json()


def pack_data(json_data, stock_price, is_call):
    data = dict()
    data['spot'] = stock_price
    data['strike'] = json_data.get('strike')
    data['t'] = json_data.get('daysBeforeExpiration')
    data['v'] = json_data.get('impliedVolatility')
    data['bid'] = json_data.get('bid')
    data['ask'] = json_data.get('ask')
    data['lastTradeDateTime'] = json_data.get('lastTradeDateTime')
    data['rf'] = 0.055
    data['cp'] = 1 if is_call else -1
    return data


def process_data(response):
    calls = dict()
    exp_dates = list()
    stock_price = extract_spot(response)
    for data in response.get('data'):
        expirationDate = data.get('expirationDate')
        exp_dates.append(expirationDate)

        calls[expirationDate] = dict()
        calls[expirationDate]['CALL'] = list()
        calls[expirationDate]['PUT'] = list()

        for call in data.get('options').get('CALL'):
            call_data = pack_data(call, stock_price, True)
            calls[expirationDate]['CALL'].append(call_data)

        for put in data.get('options').get('PUT'):
            put_data = pack_data(put, stock_price, False)
            calls[expirationDate]['PUT'].append(put_data)
    return calls


our_data = Data(
    spot=49.46,
    strike=41.5,
    time=8,
    volatility=0.9,
    rate=0.055,
    mode=1,
    dt=1/365,
    ask=0.32,
    bid=0.26
)


def main(use_our_data=True, call_option=True):
    # need to get spot anyway
    if not use_our_data:
        response = get_raw_data(API_URL, SHARE_NAME, API_TOKEN)
        spot = extract_spot(response)
        calls = process_data(response)
    else:
        k = calculate_k_arg(our_data.ask, our_data.bid)
        new_v = calculate_volatility(our_data.volatility, k, our_data.dt)
        mode = our_data.mode if call_option else -our_data.mode

        print('Vanilla black scholes:\t', black_scholes(
            spot=our_data.spot,
            strike=our_data.strike,
            time=our_data.time,
            v=our_data.volatility,
            rf=our_data.rate,
            cp=mode), sep='')

        print('With recalculated volatility:\t', black_scholes(
            spot=our_data.spot,
            strike=our_data.strike,
            time=our_data.time,
            v=new_v,
            rf=our_data.rate,
            cp=mode), sep='')

        to_plot_bs = list()
        to_plot_dt = list()

        for dt in range(0, 10, 1):
            k = calculate_k_arg(our_data.ask, our_data.bid)
            new_v = calculate_volatility(our_data.volatility, k, dt / 3650)
            to_plot_bs.append(black_scholes(
                spot=our_data.spot,
                strike=our_data.strike,
                time=our_data.time,
                v=new_v,
                rf=our_data.rate,
                cp=mode))
            to_plot_dt.append(dt / 3650)

        plt.plot(to_plot_dt,
                 to_plot_bs,
                 color='magenta',
                 label='value of {} option'.format('call' if mode == 1 else 'put'))
        plt.xlabel('delta time')
        plt.ylabel('black scholes model ans')
        plt.title(
            'Change of black scholes model price with change of delta t'
        )
        plt.legend()
        plt.show()


if __name__ == "__main__":
    main(call_option=True)
