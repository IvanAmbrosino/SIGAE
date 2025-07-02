CREATE TABLE `users` (
  `id` varchar(255) PRIMARY KEY,
  `username` varchar(255) UNIQUE,
  `password_hash` varchar(255),
  `email` varchar(255) UNIQUE,
  `full_name` varchar(255),
  `is_active` boolean,
  `created_at` timestamp,
  `updated_at` timestamp
);

CREATE TABLE `roles` (
  `id` varchar(255) PRIMARY KEY,
  `name` varchar(255) UNIQUE,
  `description` text
);

CREATE TABLE `user_roles` (
  `user_id` varchar(255),
  `role_id` varchar(255),
  `primary` key(user_id,role_id)
);

CREATE TABLE `permissions` (
  `id` varchar(255) PRIMARY KEY,
  `name` varchar(255) UNIQUE,
  `description` text
);

CREATE TABLE `role_permissions` (
  `role_id` varchar(255),
  `permission_id` varchar(255),
  `primary` key(role_id,permission_id)
);

CREATE TABLE `ground_stations` (
  `id` varchar(255) PRIMARY KEY,
  `name` varchar(255),
  `location` varchar(255),
  `latitude` decimal,
  `longitude` decimal,
  `altitude` decimal,
  `description` text,
  `is_active` boolean
);

CREATE TABLE `antennas` (
  `id` varchar(255) PRIMARY KEY,
  `ground_station_id` varchar(255),
  `name` varchar(255),
  `model` varchar(255),
  `min_elevation` decimal,
  `operational_status` enum(operational,maintenance,out_of_service),
  `quality_level` enum(high,medium,low),
  `is_active` boolean,
  `created_at` timestamp,
  `updated_at` timestamp
);

CREATE TABLE `antenna_capabilities` (
  `id` varchar(255) PRIMARY KEY,
  `antenna_id` varchar(255),
  `frequency_band` enum(S,X,Ku,Ka,other),
  `min_frequency` decimal,
  `max_frequency` decimal,
  `polarization` enum(linear,circular,dual),
  `data_rate` decimal
);

CREATE TABLE `satellites` (
  `id` varchar(255) PRIMARY KEY,
  `name` varchar(255),
  `norad_id` varchar(255) UNIQUE,
  `priority_level` enum(critical,high,medium,low),
  `description` text,
  `is_active` boolean,
  `created_at` timestamp,
  `updated_at` timestamp
);

CREATE TABLE `satellite_requirements` (
  `id` varchar(255) PRIMARY KEY,
  `satellite_id` varchar(255),
  `frequency_band` enum(S,X,Ku,Ka,other),
  `min_frequency` decimal,
  `max_frequency` decimal,
  `polarization` enum(linear,circular,dual),
  `min_elevation` decimal,
  `min_duration` int
);

CREATE TABLE `satellite_antenna_compatibility` (
  `satellite_id` varchar(255),
  `antenna_id` varchar(255),
  `primary` key(satellite_id,antenna_id)
);

CREATE TABLE `tle_data` (
  `id` varchar(255) PRIMARY KEY,
  `satellite_id` varchar(255),
  `line1` varchar(255),
  `line2` varchar(255),
  `epoch` timestamp,
  `source` enum(spacetrack,manual,api),
  `is_valid` boolean,
  `created_at` timestamp
);

CREATE TABLE `activities` (
  `id` varchar(255) PRIMARY KEY,
  `satellite_id` varchar(255),
  `orbit_number` varchar(255),
  `start_time` timestamp,
  `max_elevation_time` timestamp,
  `end_time` timestamp,
  `duration` int,
  `status` enum(new,assigned,unassigned,pending,authorized,planned,modified,updated,critical),
  `priority` enum(critical,high,medium,low),
  `created_at` timestamp,
  `updated_at` timestamp
);

CREATE TABLE `activity_assignments` (
  `id` varchar(255) PRIMARY KEY,
  `activity_id` varchar(255),
  `antenna_id` varchar(255),
  `assigned_by` varchar(255),
  `assigned_at` timestamp,
  `is_confirmed` boolean,
  `confirmed_by` varchar(255),
  `confirmed_at` timestamp
);

CREATE TABLE `activity_requirements` (
  `id` varchar(255) PRIMARY KEY,
  `activity_id` varchar(255),
  `frequency_band` enum(S,X,Ku,Ka,other),
  `min_frequency` decimal,
  `max_frequency` decimal,
  `polarization` enum(linear,circular,dual)
);

CREATE TABLE `reservations` (
  `id` varchar(255) PRIMARY KEY,
  `antenna_id` varchar(255),
  `start_time` timestamp,
  `end_time` timestamp,
  `purpose` enum(maintenance,client,other),
  `description` text,
  `requested_by` varchar(255),
  `approved_by` varchar(255),
  `status` enum(pending,approved,rejected,completed),
  `created_at` timestamp,
  `updated_at` timestamp
);

CREATE TABLE `system_configurations` (
  `id` varchar(255) PRIMARY KEY,
  `config_key` varchar(255) UNIQUE,
  `config_value` text,
  `data_type` enum(string,number,boolean,json),
  `description` text,
  `updated_by` varchar(255),
  `updated_at` timestamp
);

CREATE TABLE `notifications` (
  `id` varchar(255) PRIMARY KEY,
  `user_id` varchar(255),
  `title` varchar(255),
  `message` text,
  `is_read` boolean,
  `notification_type` enum(activity,reservation,system,alert),
  `related_entity_type` enum(activity,reservation,antenna,satellite,none),
  `related_entity_id` varchar(255),
  `created_at` timestamp
);

CREATE TABLE `activity_history` (
  `id` varchar(255) PRIMARY KEY,
  `activity_id` varchar(255),
  `changed_by` varchar(255),
  `change_type` enum(create,update,status_change,assignment),
  `old_values` json,
  `new_values` json,
  `changed_at` timestamp
);

ALTER TABLE `user_roles` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `user_roles` ADD FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`);

ALTER TABLE `role_permissions` ADD FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`);

ALTER TABLE `role_permissions` ADD FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`);

ALTER TABLE `antennas` ADD FOREIGN KEY (`ground_station_id`) REFERENCES `ground_stations` (`id`);

ALTER TABLE `antenna_capabilities` ADD FOREIGN KEY (`antenna_id`) REFERENCES `antennas` (`id`);

ALTER TABLE `satellite_requirements` ADD FOREIGN KEY (`satellite_id`) REFERENCES `satellites` (`id`);

ALTER TABLE `satellite_antenna_compatibility` ADD FOREIGN KEY (`satellite_id`) REFERENCES `satellites` (`id`);

ALTER TABLE `satellite_antenna_compatibility` ADD FOREIGN KEY (`antenna_id`) REFERENCES `antennas` (`id`);

ALTER TABLE `tle_data` ADD FOREIGN KEY (`satellite_id`) REFERENCES `satellites` (`id`);

ALTER TABLE `activities` ADD FOREIGN KEY (`satellite_id`) REFERENCES `satellites` (`id`);

ALTER TABLE `activity_assignments` ADD FOREIGN KEY (`activity_id`) REFERENCES `activities` (`id`);

ALTER TABLE `activity_assignments` ADD FOREIGN KEY (`antenna_id`) REFERENCES `antennas` (`id`);

ALTER TABLE `activity_assignments` ADD FOREIGN KEY (`assigned_by`) REFERENCES `users` (`id`);

ALTER TABLE `activity_assignments` ADD FOREIGN KEY (`confirmed_by`) REFERENCES `users` (`id`);

ALTER TABLE `activity_requirements` ADD FOREIGN KEY (`activity_id`) REFERENCES `activities` (`id`);

ALTER TABLE `reservations` ADD FOREIGN KEY (`antenna_id`) REFERENCES `antennas` (`id`);

ALTER TABLE `reservations` ADD FOREIGN KEY (`requested_by`) REFERENCES `users` (`id`);

ALTER TABLE `reservations` ADD FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`);

ALTER TABLE `system_configurations` ADD FOREIGN KEY (`updated_by`) REFERENCES `users` (`id`);

ALTER TABLE `notifications` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `activity_history` ADD FOREIGN KEY (`activity_id`) REFERENCES `activities` (`id`);

ALTER TABLE `activity_history` ADD FOREIGN KEY (`changed_by`) REFERENCES `users` (`id`);
