graphite_url = 'http://graphitemachine'
anthracite_url = None
listen_host = '0.0.0.0'  # defaults to "all interfaces"
listen_port = 8080
filename_metrics = 'metrics.json'
log_file = 'graph-explorer.log'

app_name         = "graph-explorer" # name that will prefix stats shipped to statsd.
statsd_params    = { "host"        : "127.0.0.1",
                     "port"        : 8125,
                     "sample_rate" : 1}
