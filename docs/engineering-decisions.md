# Engineering decisions

- **PySpark and Delta Lake:** support scalable transformations and transactional lakehouse tables.
- **Configuration-driven ingestion:** new sources use YAML rather than bespoke readers.
- **Medallion architecture:** separates raw capture, validation, and analytics-facing models.
- **Quarantine:** invalid records retain failure context instead of being silently discarded.
- **PostgreSQL:** planned serving layer, not a replacement for Delta storage.
- **Kafka and cloud deployment:** intentionally excluded from the local, time-boxed scope.
