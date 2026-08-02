from typing import TypedDict


class BootstrapResponse(TypedDict):
  chips: list[dict]
  events: list[dict]
  game_settings: dict
  game_config: dict
  phases: list[dict]
  teams: list[dict]
  total_players: int
  element_stats: list[dict]
  element_types: list[dict]
  elements: list[dict]


class Fixture(TypedDict):
  code: int
  event: int
  finished: bool
  finished_provisional: bool
  id: int
  kickoff_time: str
  minutes: int
  provisional_start_time: bool
  started: bool
  team_a: int
  team_a_score: int | None
  team_h: int
  team_h_score: int | None
  stats: list
  team_h_difficulty: int
  team_a_difficulty: int
  pulse_id: int
