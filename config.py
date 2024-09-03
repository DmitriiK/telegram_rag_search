from datetime import timedelta

# distance in timedelta for topic candidate messages, - we are conidering 2 hours before and 2 hours after messages
near_messages_time_delta = timedelta(hours=2)

# OR we are conidering 2 messages before and 3 messages after
near_messages_number_of_messages_delta = 3