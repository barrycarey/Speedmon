from dataclasses import dataclass
from typing import Text, Optional

from pydantic import BaseModel


class SpeedTestResult(BaseModel):
    latency: float
    download: float
    upload: float
    server_id: int
    server_name: Text
    server_country: Text
    server_location: Text
    packetloss: Optional[float] = None
    jitter: Optional[int] = None

    def __init__(self, **kwargs):
        kwargs['latency'] = kwargs['ping']['latency']
        if 'jitter' in kwargs:
            kwargs['jitter'] = kwargs['ping']['jitter']
        if 'packetloss' in kwargs:
            kwargs['packetloss'] = kwargs['packetloss']

        kwargs['download'] = kwargs['download']['bandwidth']
        kwargs['upload'] = kwargs['upload']['bandwidth']
        kwargs['server_id'] = kwargs['server']['id']
        kwargs['server_name'] = kwargs['server']['name']
        kwargs['server_country'] = kwargs['server']['country']
        kwargs['server_location'] = kwargs['server']['location']

        super().__init__(**kwargs)