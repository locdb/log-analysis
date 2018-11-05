# depends on locdb ssh entry
mkdir -p data
scp locdb:/home/anlausch/.pm2/logs/loc-db-production-out-6.log data/

# Continuous, messy data
# scp locdb:/home/anlausch/.pm2/logs/loc-db-production-out-10.log data/
# scp locdb:/home/anlausch/.pm2/logs/loc-db-production-out-4.log data/

# First evaluation (JCDL Paper)
# scp locdb:/home/anlausch/.pm2/logs/loc-db-production-out-1.log data/
