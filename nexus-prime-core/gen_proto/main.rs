fn main() {
    let proto_includes = vec![
        "../proto",
        "../third_party",
        "../third_party/google/protobuf",
    ];
    tonic_build::configure()
        .protoc_arg("--experimental_allow_proto3_optional")
        .build_client(true)
        .build_server(true)
        .out_dir("../src/fabric_proto")
        .compile(&["../proto/fabric.proto"], &proto_includes)
        .expect("Failed to generate protobuf code");
    println!("Protobuf code generation succeeded.");
}
