#include "micipsa_perception/pointcloud/pointcloud_processor.h"

// =====================================
//              Constructor
// =====================================
PointCloudProcessor::PointCloudProcessor() : params_{} {
}

// ============================================
//         Pointcloud Process Pipeline
// ============================================
PcProcessingResult PointCloudProcessor::process(const pcl::PointCloud<pcl::PointXYZI>::Ptr &input,
                                                const Eigen::Matrix4f &transform_matrix) {
    PcProcessingResult result;

    // 1. Crop in sensor frame
    result.cropped = apply_cropbox(input);

    // 2. Downsample BEFORE transform
    result.voxel_filtered = apply_voxel(result.cropped);

    // 3. Transform reduced cloud
    result.voxel_filtered = apply_transform(result.voxel_filtered, transform_matrix);

    // 4. Denoise
    result.sor_filtered = apply_sor(result.voxel_filtered);

    // 5. Plane segmentation
    if (params_.is_3d) {
        result.no_ground = segment_plane(result.sor_filtered);
    }

    return result;
}

// ==============================================
//          Pointcloud Process Functions
// ==============================================
pcl::PointCloud<pcl::PointXYZI>::Ptr PointCloudProcessor::apply_cropbox(
        const pcl::PointCloud<pcl::PointXYZI>::Ptr &input) {
    pcl::PointCloud<pcl::PointXYZI>::Ptr output(new pcl::PointCloud<pcl::PointXYZI>());

    pcl::CropBox<pcl::PointXYZI> crop;
    crop.setInputCloud(input);
    crop.setMin(
            Eigen::Vector4f(params_.x_crop_min, params_.y_crop_min, params_.z_crop_min, POINT_W));
    crop.setMax(
            Eigen::Vector4f(params_.x_crop_max, params_.y_crop_max, params_.z_crop_max, POINT_W));
    crop.filter(*output);

    return output;
}

pcl::PointCloud<pcl::PointXYZI>::Ptr PointCloudProcessor::apply_voxel(
        const pcl::PointCloud<pcl::PointXYZI>::Ptr &input) {
    pcl::PointCloud<pcl::PointXYZI>::Ptr output(new pcl::PointCloud<pcl::PointXYZI>());

    pcl::VoxelGrid<pcl::PointXYZI> voxel;
    voxel.setInputCloud(input);
    voxel.setLeafSize(params_.voxel_leaf_size, params_.voxel_leaf_size, params_.voxel_leaf_size);
    voxel.filter(*output);

    return output;
}

pcl::PointCloud<pcl::PointXYZI>::Ptr PointCloudProcessor::apply_transform(
        const pcl::PointCloud<pcl::PointXYZI>::Ptr &input,
        const Eigen::Matrix4f &transform_matrix) {
    pcl::PointCloud<pcl::PointXYZI>::Ptr output(new pcl::PointCloud<pcl::PointXYZI>());

    pcl::transformPointCloud(*input, *output, transform_matrix);

    return output;
}

pcl::PointCloud<pcl::PointXYZI>::Ptr PointCloudProcessor::apply_sor(
        const pcl::PointCloud<pcl::PointXYZI>::Ptr &input) {
    pcl::PointCloud<pcl::PointXYZI>::Ptr output(new pcl::PointCloud<pcl::PointXYZI>());

    pcl::StatisticalOutlierRemoval<pcl::PointXYZI> sor;
    sor.setInputCloud(input);
    sor.setMeanK(params_.sor_mean_k);
    sor.setStddevMulThresh(params_.sor_stddev_multhresh);
    sor.filter(*output);

    return output;
}

pcl::PointCloud<pcl::PointXYZI>::Ptr PointCloudProcessor::segment_plane(
        const pcl::PointCloud<pcl::PointXYZI>::Ptr &input) {
    pcl::PointCloud<pcl::PointXYZI>::Ptr obstacles(new pcl::PointCloud<pcl::PointXYZI>());

    pcl::SACSegmentation<pcl::PointXYZI> seg;
    pcl::PointIndices::Ptr inliers(new pcl::PointIndices);
    pcl::ModelCoefficients::Ptr coefficients(new pcl::ModelCoefficients);

    Eigen::Vector3f axis = Eigen::Vector3f::UnitZ();
    if (params_.plane_axis == "UnitX") {
        axis = Eigen::Vector3f::UnitX();
    } else if (params_.plane_axis == "UnitY") {
        axis = Eigen::Vector3f::UnitY();
    } else if (params_.plane_axis == "UnitZ") {
        axis = Eigen::Vector3f::UnitZ();
    }

    int model_type = pcl::SACMODEL_PLANE;
    if (params_.model_type == "SACMODEL_PARALLEL_PLANE") {
        model_type = pcl::SACMODEL_PARALLEL_PLANE;
    } else if (params_.model_type == "SACMODEL_PERPENDICULAR_PLANE") {
        model_type = pcl::SACMODEL_PERPENDICULAR_PLANE;
    }

    int method_type = pcl::SAC_RANSAC;
    if (params_.method_type == "SAC_LMEDS") {
        method_type = pcl::SAC_LMEDS;
    } else if (params_.method_type == "SAC_MSAC") {
        method_type = pcl::SAC_MSAC;
    } else if (params_.method_type == "SAC_RRANSAC") {
        method_type = pcl::SAC_RRANSAC;
    }

    seg.setAxis(axis);
    seg.setEpsAngle(params_.eps_angle);
    seg.setOptimizeCoefficients(params_.optimize_coefficients);
    seg.setModelType(model_type);
    seg.setMethodType(method_type);
    seg.setMaxIterations(params_.plane_max_iterations);
    seg.setDistanceThreshold(params_.plane_distance_threshold);
    seg.setInputCloud(input);

    seg.segment(*inliers, *coefficients);

    if (inliers->indices.empty()) {
        return input;
    }

    pcl::ExtractIndices<pcl::PointXYZI> extract;
    extract.setInputCloud(input);
    extract.setIndices(inliers);
    extract.setNegative(true);
    extract.filter(*obstacles);

    return obstacles;
}

// ==============================================
//          Pointcloud Helpers Functions
// ==============================================
void PointCloudProcessor::update_params(const PcProcessingParams &params) {
    params_ = params;
}

PcProcessingParams PointCloudProcessor::params() {
    return params_;
}