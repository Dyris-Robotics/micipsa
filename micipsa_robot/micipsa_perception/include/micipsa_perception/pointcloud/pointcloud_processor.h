#ifndef MICIPSA_PERCEPTION__POINTCLOUD_PROCESSOR_H_
#define MICIPSA_PERCEPTION__POINTCLOUD_PROCESSOR_H_

#include <string>

#include <pcl/common/common.h>
#include <pcl/common/transforms.h>
#include <pcl/filters/crop_box.h>
#include <pcl/filters/extract_indices.h>
#include <pcl/filters/passthrough.h>
#include <pcl/filters/statistical_outlier_removal.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl/segmentation/extract_clusters.h>
#include <pcl/segmentation/sac_segmentation.h>

struct PcProcessingParams {
    // Input / output
    bool is_3d = true;

    // Voxel Grid
    float voxel_leaf_size = 0.05f;

    // Crop Box
    float x_crop_min = -2.0f;
    float x_crop_max = 2.0f;
    float y_crop_min = -2.0f;
    float y_crop_max = 2.0f;
    float z_crop_min = -1.0f;
    float z_crop_max = 1.0f;

    // SOR
    int sor_mean_k = 50;
    float sor_stddev_multhresh = 1.0;

    // Plane Segmentation
    std::string plane_axis = "UnitX";
    float eps_angle = (10.0f * M_PI) / 180.0f;
    bool optimize_coefficients = true;
    std::string model_type = "SACMODEL_PARALLEL_PLANE";
    std::string method_type = "SAC_RANSAC";
    int plane_max_iterations = 100;
    float plane_distance_threshold = 0.02f;
};

struct PcProcessingResult {
    pcl::PointCloud<pcl::PointXYZI>::Ptr voxel_filtered;
    pcl::PointCloud<pcl::PointXYZI>::Ptr cropped;
    pcl::PointCloud<pcl::PointXYZI>::Ptr sor_filtered;
    pcl::PointCloud<pcl::PointXYZI>::Ptr no_ground;
};

constexpr float POINT_W = 1.0f;  // w = 1.0 -> point | w = 0.0 -> direction vector

class PointCloudProcessor {
 public:
    PointCloudProcessor();

    // ============================================
    //         Pointcloud Process Pipeline
    // ============================================
    PcProcessingResult process(const pcl::PointCloud<pcl::PointXYZI>::Ptr &input,
                               const Eigen::Matrix4f &transform_matrix);

    // ==============================================
    //          Pointcloud Helpers Functions
    // ==============================================
    void update_params(const PcProcessingParams &params);
    PcProcessingParams params();

 private:
    PcProcessingParams params_;

    // ==============================================
    //          Pointcloud Process Functions
    // ==============================================
    pcl::PointCloud<pcl::PointXYZI>::Ptr apply_cropbox(
            const pcl::PointCloud<pcl::PointXYZI>::Ptr &input);

    pcl::PointCloud<pcl::PointXYZI>::Ptr apply_voxel(
            const pcl::PointCloud<pcl::PointXYZI>::Ptr &input);

    pcl::PointCloud<pcl::PointXYZI>::Ptr apply_transform(
            const pcl::PointCloud<pcl::PointXYZI>::Ptr &input,
            const Eigen::Matrix4f &transform_matrix);

    pcl::PointCloud<pcl::PointXYZI>::Ptr apply_sor(
            const pcl::PointCloud<pcl::PointXYZI>::Ptr &input);

    pcl::PointCloud<pcl::PointXYZI>::Ptr segment_plane(
            const pcl::PointCloud<pcl::PointXYZI>::Ptr &input);
};

#endif  // MICIPSA_PERCEPTION__POINTCLOUD_PROCESSOR_H_