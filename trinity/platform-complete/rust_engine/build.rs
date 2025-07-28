// nexus-prime-core/build.rs

fn main() {
    let proto_includes = vec![
        "proto",
        "third_party",
        "third_party/google/protobuf",
    ];
    println!("cargo:rerun-if-changed=proto/fabric.proto");
    println!("cargo:rerun-if-changed=proto");
    println!("cargo:rerun-if-changed=third_party");
    println!("cargo:rerun-if-changed=third_party/google/protobuf");
    match tonic_build::configure()
        .protoc_arg("--experimental_allow_proto3_optional")
        .build_client(true)
        .build_server(true)
        .out_dir("src/fabric_proto")
        .compile(&["proto/fabric.proto"], &proto_includes) {
        Ok(_) => println!("Protobuf code generation succeeded."),
        Err(e) => {
            println!("Protobuf code generation failed: {e}");
            std::process::exit(1);
        }
    }
}
