import logging

def setup_logger():
    logger = logging.getLogger('reporag')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler
    fh = logging.FileHandler('reporag.log')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

logger = setup_logger()
