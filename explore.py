import json
import pandas as pd

if __name__ == '__main__':
  data = None
  with open('./data/raw/fpl-bootstrap.json', 'r') as file:
    data = json.load(file)
  df = pd.DataFrame(data["elements"])

  first = df.iloc[0]

  for key in data:
    data_type = str(type(data[key]))
    details = None
    if data_type.find('list') != -1 or data_type.find('str') != -1:
      details = len(data[key])
    elif data_type.find('dict') != -1:
      details = ", ".join(list(data[key].keys()))
    elif data_type.find('int') != -1:
      details = data[key]
    print(f"{key} : {type(data[key])} | {details}")
