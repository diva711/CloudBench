terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  credentials = file("../../gcp-key.json")
  project     = "cloudbench-500511"
  region      = "asia-south1"
  zone        = "asia-south1-a"
}

# GCS bucket for benchmark results
resource "google_storage_bucket" "benchmark_bucket" {
  name          = "cloudbench-results-diva"
  location      = "asia-south1"
  force_destroy = true
}

# Firewall rule — allow HTTP on port 80
resource "google_compute_firewall" "allow_http" {
  name    = "cloudbench-allow-http"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "22"]
  }

  source_ranges = ["0.0.0.0/0"]
}

# GCP VM
resource "google_compute_instance" "benchmark_vm" {
  name         = "cloudbench-vm"
  machine_type = "e2-micro"
  zone         = "asia-south1-a"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
    }
  }

  network_interface {
    network = "default"
    access_config {}  # gives it a public IP
  }

  metadata = {
    ssh-keys = "ubuntu:${file("~/.ssh/cloudbench-gcp.pub")}"
  }

  tags = ["http-server"]
}

output "vm_public_ip" {
  value = google_compute_instance.benchmark_vm.network_interface[0].access_config[0].nat_ip
}

output "bucket_name" {
  value = google_storage_bucket.benchmark_bucket.name
}