resource "aws_sqs_queue" "neoevents_dlq" {
  name                      = "neoevents-email-queue-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 days (Maximum)
}

resource "aws_sqs_queue" "neoevents_queue" {
  name                      = "neoevents-email-queue-${var.environment}"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 345600 # 4 days
  receive_wait_time_seconds = 0
  visibility_timeout_seconds = 300 # Should be >= Lambda timeout

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.neoevents_dlq.arn
    maxReceiveCount     = 5
  })
}

output "sqs_queue_url" {
  value = aws_sqs_queue.neoevents_queue.id
}

output "sqs_queue_arn" {
  value = aws_sqs_queue.neoevents_queue.arn
}
