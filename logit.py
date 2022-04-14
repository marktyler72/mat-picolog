import logger

dl = logger.DataLogger(use_sd=True)

try:
    dl.config_hw()
    dl.run()
except KeyboardInterrupt:
    dl.deinit("User requested shutdown")
except Exception as e:
    dl.deinit("?? Error: " + str(e))
