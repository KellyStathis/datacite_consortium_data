This project exports account data for a DataCite consortium's consortium organizations and their repositories.

## Configuration

Create an .env file with the consortium's credentials (`CONSORTIUM_ID` and `CONSORTIUM_PASS`). 

Set `TEST_INSTANCE=true` to run using test (api.test.datacite.org). Otherwise, the script will default to the production API (api.datacite.org).

Example .env:

```
CONSORTIUM_ID=consortium_example_id
CONSORTIUM_PASS=consortium_example_pass
TEST_INSTANCE=false
```

## Usage

`pipenv install`  
`pipenv run python consortium_data.py`


## Tips

The JSON output can be uploaded to OpenRefine. Select Parse data as: JSON files, then click the first `{` to specify the record path.

