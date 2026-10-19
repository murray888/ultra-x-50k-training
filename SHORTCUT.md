# Weekly upload Shortcut (iPhone)

Builds a list of the last 14 days of runs from Apple Health and sends it to GitHub. Safe to run more than once: runs are merged by start time.
Set `ATHLETE` to `murray` or `rich`, and use your own GitHub token.

## Build it (Shortcuts app > + New Shortcut)
1. **Text**: your GitHub token. Name the variable `TOKEN`.
2. **Text**: `murray` (or `rich`). Name it `ATHLETE`.
3. **Adjust Date**: current date, subtract 14 days. Name it `SINCE`.
4. **Find Health Samples** where *Type is Workouts*, *Start Date is after* `SINCE`, *Workout Type is Running* (also add Trail Running if you use it). Sort by Start Date, oldest first.
5. **Repeat with Each** item in the results:
   1. **Get Details of Health Sample**: Start Date, End Date, Duration, Distance. Keep them as variables.
   2. **Find Health Samples**: *Type is Heart Rate*, *Start Date is between* the workout's Start Date and End Date.
   3. **Calculate Statistics**: Average (name it `AVG`) and Maximum (name it `MAX`) of the heart rate values.
   4. **Dictionary**:
      - `start` (Text): Start Date formatted ISO 8601 (Format Date > Custom: `yyyy-MM-dd'T'HH:mm:ss`)
      - `distance_km` (Number): Distance in kilometres
      - `moving_s` (Number): Duration in seconds
      - `avg_hr` (Number): `AVG`
      - `max_hr` (Number): `MAX`
   5. **Add to Variable** `RUNS`.
6. **Dictionary** `BODY`: `event_type` = `runs-upload`; `client_payload` (Dictionary) = `athlete` (Text) `ATHLETE`, `runs` (List) `RUNS`.
7. **Get Contents of URL**:
   - URL `https://api.github.com/repos/murray888/ultra-x-50k-training/dispatches`
   - Method POST, Request Body JSON = `BODY`
   - Headers: `Authorization` = `Bearer ` + `TOKEN`; `Accept` = `application/vnd.github+json`; `X-GitHub-Api-Version` = `2022-11-28`
8. **Show Notification**: "Runs uploaded". GitHub returns an empty response (HTTP 204) on success.

## Automate it
Shortcuts > Automation > + > Time of Day > Sunday 19:00 > Run Shortcut > select it > **Run Immediately** (turn off "Notify When Run" if you like).
The phone must be unlocked-capable and the Watch synced to Health beforehand.

## Troubleshooting
* Nothing appears: Actions tab > Update training site. A 404 or 403 from GitHub means the token is wrong or lacks Contents write on the repo.
* Distance in miles: set the Distance detail to kilometres in step 5.1.
* Large uploads: the payload limit is 65 KB, which is far more than 14 days of runs.
