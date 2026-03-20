"""
Microsoft Foundry Agent Workflow - Podcast Generator
生成播客内容的工作流脚本
"""

import argparse
import os
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentReference,
    ResponseStreamEventType,
    WorkflowAgentDefinition,
    ItemType
)
from openai.types.responses.response_input_param import ResponseInputParam


def safe_get_agent_name_from_item(item):
    """从 item 中安全获取 agent 名称"""
    # 1) workflow_action：一般用 action_id 当作"名字"
    item_type = getattr(item, "type", None) if not isinstance(item, dict) else item.get("type")
    if item_type == "workflow_action":
        return getattr(item, "action_id", None) if not isinstance(item, dict) else item.get("action_id")

    # 2) message：从 created_by.agent.name 取
    if isinstance(item, dict):
        return (item.get("created_by") or {}).get("agent", {}).get("name")

    created_by = getattr(item, "created_by", None) or {}
    if isinstance(created_by, dict):
        return (created_by.get("agent") or {}).get("name")

    # created_by 也可能是对象
    agent = getattr(created_by, "agent", None)
    return getattr(agent, "name", None)


def extract_text_from_response(response):
    """从响应中提取文本内容"""
    texts = []
    for output_item in response.output:
        # 检查是否是 message 类型
        if getattr(output_item, 'type', None) == 'message':
            content = getattr(output_item, 'content', [])
            if content:
                for content_part in content:
                    # 检查是否是 output_text 类型
                    if getattr(content_part, 'type', None) == 'output_text':
                        text = getattr(content_part, 'text', '')
                        if text:
                            texts.append(text)
    return texts


def save_podcast_content(content: str, output_dir: str = "podcast") -> str:
    """保存播客内容到文件"""
    podcast_dir = Path(output_dir)
    podcast_dir.mkdir(exist_ok=True)
    
    file_uuid = str(uuid.uuid4())[:8]  # 使用前8位UUID
    filename = f"2p_podcast_{file_uuid}.txt"
    file_path = podcast_dir / filename
    
    file_path.write_text(content, encoding="utf-8")
    print(f"内容已保存到文件: {file_path}")
    return str(file_path)


def run_podcast_workflow(
    endpoint: str,
    workflow_yaml_path: str,
    input_topic: str,
    workflow_name: str = "podcast-orch-workflow"
):
    """
    运行播客生成工作流
    
    Args:
        endpoint: Azure AI Foundry 项目端点
        workflow_yaml_path: 工作流 YAML 文件路径
        input_topic: 播客主题
        workflow_name: 工作流名称
    """
    # print the azure credentail like client id ,tenant id, secret
    print(f"AZURE_CLIENT_ID: {os.getenv('AZURE_CLIENT_ID')}")
    print(f"AZURE_CLIENT_SECRET: {os.getenv('AZURE_CLIENT_SECRET')}")
    print(f"AZURE_TENANT_ID: {os.getenv('AZURE_TENANT_ID')}")
    print(f"AZURE_SUBSCRIPTION_ID: {os.getenv('AZURE_SUBSCRIPTION_ID')}")

    content = ""
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
        project_client.get_openai_client() as openai_client,
    ):
        
        print(credential.get_token("https://cognitiveservices.azure.com/.default"))
        # 从文件读取 workflow_yaml
        with open(workflow_yaml_path, "r", encoding="utf-8") as f:
            workflow_yaml = f.read()

        workflow = project_client.agents.create_version(
            agent_name=workflow_name,
            definition=WorkflowAgentDefinition(workflow=workflow_yaml),
        )

        print(f"Agent created (id: {workflow.id}, name: {workflow.name}, version: {workflow.version})")

        conversation = openai_client.conversations.create()
        print(f"Created conversation (id: {conversation.id})")

        input_list: ResponseInputParam = [input_topic, "Yes"]

        stream = openai_client.responses.create(
            conversation=conversation.id,
            extra_body={"agent": {"name": workflow.name, "type": "agent_reference"}},
            input=input_list[0],
            stream=True,
            metadata={"x-ms-debug-mode-enabled": "1"},
        )

        status = 0
        for event in stream:
            if event.type == ResponseStreamEventType.RESPONSE_OUTPUT_ITEM_ADDED:
                name = safe_get_agent_name_from_item(event.item)
                if getattr(event.item, "type", None) == "message" and name == "podcast-search-agent":
                    status = 0
                elif getattr(event.item, "type", None) == "message" and name == "podcast-content-agent":
                    status = 1
                else:
                    status = 2

            if event.type == ResponseStreamEventType.RESPONSE_OUTPUT_TEXT_DONE:
                if status == 1:
                    content = event.text
                    save_podcast_content(content)

                if "Yes" in event.text and status == 2:
                    response = openai_client.responses.create(
                        conversation=conversation.id,
                        extra_body={"agent": {"name": workflow.name, "type": "agent_reference"}},
                        input="Yes",
                        stream=False,
                        metadata={"x-ms-debug-mode-enabled": "1"},
                    )

                    print("User confirmed saving the script. Exiting workflow.")
                    break
    
    return content


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="生成播客内容的工作流脚本")
    parser.add_argument(
        "--topic", "-t",
        type=str,
        required=True,
        help="播客主题"
    )
    parser.add_argument(
        "--endpoint", "-e",
        type=str,
        default="https://kinfey-ai-foundry.services.ai.azure.com/api/projects/kinfey-ai-foundry-proj",
        help="Azure AI Foundry 项目端点"
    )
    parser.add_argument(
        "--yaml", "-y",
        type=str,
        default="./yaml/yaml_c3e43833.yaml",
        help="工作流 YAML 文件路径"
    )
    args = parser.parse_args()
    
    # 加载环境变量
    load_dotenv(".env")
    
    # 运行工作流
    result = run_podcast_workflow(
        endpoint=args.endpoint,
        workflow_yaml_path=args.yaml,
        input_topic=args.topic
    )
    
    if result:
        print("播客内容生成完成!")


if __name__ == "__main__":
    main()
