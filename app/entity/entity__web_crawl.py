from pydantic import BaseModel
from typing import List, Optional


class SingleWebCrawlRequest(BaseModel):
    target_url: str
    json_result_format: str
    clue: Optional[str] = None
    current_transaction_attempt: Optional[int] = 1
    max_retry: Optional[int] = 1


class IndonesianCitizenCrawlDetailResponse(BaseModel):
    kota: str
    provinsi: str
    jumlah_penduduk: str

class IndonesianCitizenCrawlResponse(BaseModel):
    penduduk: List[IndonesianCitizenCrawlDetailResponse]
    # choices: List[str]

class CityDensityData(BaseModel):
    no: int
    city: str
    province: str
    area_km2: float
    population_2023: int
    density_per_km2: int
    references: Optional[str] = None

class CityDensityTable(BaseModel):
    rows: List[CityDensityData]