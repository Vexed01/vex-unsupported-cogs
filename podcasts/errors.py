class PodcastError(Exception):
    """Base class for all podcast exceptions."""
    pass

class NoResults(PodcastError):
    """Raised when no results are found."""
    pass