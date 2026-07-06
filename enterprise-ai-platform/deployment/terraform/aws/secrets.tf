locals {
  database_url = "postgresql+psycopg://${var.database_username}:${var.database_password}@${aws_db_instance.postgres.address}:5432/${var.database_name}"
}

resource "aws_secretsmanager_secret" "api" {
  name        = "${local.name_prefix}/api"
  description = "Runtime secrets for the EAKP API."
}

resource "aws_secretsmanager_secret_version" "api" {
  secret_id = aws_secretsmanager_secret.api.id
  secret_string = jsonencode({
    EAKP_DATABASE_URL   = local.database_url
    EAKP_JWT_SECRET_KEY = var.jwt_secret_key
  })
}
