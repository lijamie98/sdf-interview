#
# If you'd like to run the web server interactively, use this file.
# Select "Run custom script" from CodeSignal's blue dropdown menu.
#

# uncomment line below to run all tests
# python3 -m unittest discover './tests' -p '*.py'

# This run the web server in the background. Note that you have a 60s execution
# limit, and the server will harakiri after 10s.
python3 solution.py &
sleep 1

curl http://localhost:8080/