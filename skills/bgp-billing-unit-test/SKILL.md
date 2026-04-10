---
name: bgp-billing-unit-test
description: 为 bgp-billing 项目编写单元测试,遵循项目测试规范。使用 Mockito、StepVerifier、WebTestClient 测试响应式代码。当用户要求编写测试、添加测试用例、测试某个类或方法时使用此 skill。
---

# BGP Billing 单元测试规范

为 bgp-billing 项目编写符合规范的单元测试。

## 核心原则

### 1. 测试分层

- **单元测试**(`*Test`): 测试单个类/方法,Mock 所有依赖,继承 `BaseUnitTest`
- **集成测试**(`*IntegrationTest`): 测试组件交互,继承 `BaseIntegrationTest`

### 2. 基类选择

**单元测试 - 继承 BaseUnitTest:**

```java
@DisplayName("PaymentGoogleService 单元测试")
class PaymentGoogleServiceTest extends BaseUnitTest {
    @Mock
    private PaymentGoogleRepository repository;
    
    @InjectMocks
    private PaymentGoogleService service;
}
```

**集成测试 - 继承 BaseIntegrationTest:**

```java
@DisplayName("VerifyController 集成测试")
class VerifyControllerIntegrationTest extends BaseIntegrationTest {
    @Autowired
    private WebTestClient webTestClient;
    
    @BeforeEach
    void setUp() {
        // 使用 reset() 重置 Mock,不使用 @DirtiesContext
        reset(appleValidateService, googleValidateService);
    }
}
```

**关键规则:**
- ⚠️ **禁止在集成测试子类中使用 `@MockBean`** - 必须在 `BaseIntegrationTest` 中定义
- 使用 `reset()` 实现测试隔离,不使用 `@DirtiesContext`

### 3. 测试结构

使用 **嵌套类 + AAA 模式**:

```java
@Nested
@DisplayName("getByOrderId 方法")
class GetByOrderId {
    
    @Test
    @DisplayName("当 orderId 存在时,应返回对应的支付记录")
    void returnsPayment_whenOrderIdExists() {
        // Given - 准备测试数据
        when(repository.findByTransactionId("GPA.1234"))
            .thenReturn(Mono.just(payment));
        
        // When & Then - 执行并验证
        StepVerifier.create(service.getByOrderId("GPA.1234"))
            .assertNext(result -> {
                assertThat(result.getTransactionId()).isEqualTo("GPA.1234");
            })
            .verifyComplete();
    }
}
```

### 4. 响应式测试

使用 `StepVerifier` 测试 Mono/Flux:

```java
// 成功场景
StepVerifier.create(service.getById(1))
    .assertNext(result -> assertThat(result.getId()).isEqualTo(1))
    .verifyComplete();

// 空结果
StepVerifier.create(service.getById(999))
    .verifyComplete();

// 错误场景
StepVerifier.create(service.getById(null))
    .expectError(IllegalArgumentException.class)
    .verify();

// 带 Context
StepVerifier.create(
    service.validate(dto)
        .contextWrite(ctx -> ctx.put("appId", 1203))
)
.verifyComplete();
```

### 5. Mock 规范

**基础 Mock:**

```java
// Mock Repository
when(repository.findById(1)).thenReturn(Mono.just(payment));
when(repository.save(any())).thenReturn(Mono.just(payment));

// Mock RPC
when(rpc.verify(anyString())).thenReturn(Mono.just(response));

// 验证调用
verify(repository).save(any(PaymentGoogle.class));
```

**Mock 静态方法** (需要 `mockito-inline`):

```java
try (MockedStatic<DateTimeUtil> mocked = mockStatic(DateTimeUtil.class)) {
    mocked.when(DateTimeUtil::currentSeconds).thenReturn(1609459200);
    
    // 执行测试
    StepVerifier.create(service.process())
        .verifyComplete();
}
```

**参数匹配最佳实践:**
- 优先使用: `any()`, `anyString()`, `anyInt()`
- 需要条件验证: `argThat(predicate)`
- 明确值时才用: `eq(value)`

### 6. 测试数据

使用 `TestDataFactory` 创建测试数据:

```java
// 使用默认值
PaymentGoogle payment = TestDataFactory.createGooglePayment();

// 自定义字段
PaymentGoogle payment = TestDataFactory.createGooglePayment(p -> {
    p.setStatus(PaymentConstant.Status.VERIFIED);
    p.setUserId("custom-user-id");
});
```

### 7. Controller 测试

使用 `TestRequestHelper` 发送请求:

```java
@Nested
@DisplayName("verify 方法")
class Verify {
    
    @Test
    @DisplayName("当请求有效时,应返回验证结果")
    void returnsResult_whenRequestValid() {
        // Given
        ValidateDto request = TestDataFactory.createValidateDto(Constant.Channel.IOS);
        when(appleValidateService.validate(any(), any(), any()))
            .thenReturn(CompletableFuture.completedFuture(response));
        
        // When & Then - 使用完整路径
        MTResponse<ValidateRespDto> mtResponse = TestRequestHelper.postToServerWithJsonForOK(
            "/billing/payment/verify", request, Map.of(), ValidateRespDto.class);
        
        assertThat(mtResponse.getData().getChannel()).isEqualTo(Constant.Channel.IOS);
    }
}
```

### 8. 各层测试要点

| 层级 | 测试重点 | 覆盖率目标 |
|------|---------|-----------|
| Service | 业务逻辑、状态流转、异常处理 | ≥ 80% |
| Controller | HTTP 请求响应、参数校验 | ≥ 70% |
| Filter | 路径匹配、参数校验、Context 设置 | ≥ 70% |
| Util | 工具方法、数据转换 | ≥ 90% |

**Repository 层:** 通常不需要单独测试,除非有复杂自定义 SQL

### 9. 常见场景处理

**Context 传递:**

```java
StepVerifier.create(
    service.methodThatUsesContext()
        .contextWrite(ctx -> StoreUtil.set(ctx, "key", value))
        .contextWrite(ctx -> ctx.put(CONTEXT_STORE_KEY, Maps.newConcurrentMap()))
)
.verifyComplete();
```

**异步调用:**

```java
StepVerifier.create(
    service.asyncMethod()
        .subscribeOn(Schedulers.immediate())
)
.verifyComplete();
```

**TrackerUtil.sendTrack 特殊语义:**
- 成功: 返回 `Mono.empty()`
- 失败: 返回 `Mono.just("error message")`

```java
// 成功场景
when(trackerUtil.sendTrack(anyString(), anyInt(), anyString()))
    .thenReturn(Mono.empty());

// 失败场景
when(trackerUtil.sendTrack(anyString(), anyInt(), anyString()))
    .thenReturn(Mono.just("error: connection timeout"));
```

### 10. 必须测试的场景

每个公共方法至少测试:

1. **正常路径**: 有效输入,验证正确输出
2. **边界条件**: 空值、null、边界值
3. **异常路径**: 无效输入、依赖失败
4. **业务规则**: 状态转换、权限检查

**项目特定场景:**
- 支付验证: 各渠道验证逻辑、重复验证、已完成订单
- RPC 调用: 成功、超时、熔断
- 状态流转: UNVERIFIED → VERIFIED → FINISHED
- 用户/App 绑定: 跨用户/App 访问拦截
- 退款处理: Apple/Google 退款回调
- 消息处理: Track/Adjust/ThinkingData

### 11. 测试最佳实践

**✅ 推荐:**
- 每个测试独立运行
- 使用 `@DisplayName` 描述测试意图
- 遵循 AAA 模式
- 使用 `TestDataFactory` 创建测试数据
- 使用 `reset()` 实现测试隔离

**❌ 避免:**
- 测试私有方法
- 使用 `Thread.sleep()` (除非缓存机制测试)
- 使用 `@DirtiesContext`
- 在单元测试中访问真实外部服务
- 硬编码敏感信息

### 12. 停止规则

如果某个测试用例修改超过 3 次还无法解决:

1. 使用 `@Disabled("需要人工检查:原因说明")` 标记
2. 添加详细注释说明:
   - 失败原因
   - 已尝试的修复方法
   - 预期行为
   - 需要检查的点
3. 继续完成其他测试用例

## 提交前检查清单

- [ ] 测试类命名符合规范 (`*Test` 或 `*IntegrationTest`)
- [ ] 每个测试方法有 `@DisplayName` 注解
- [ ] 测试遵循 AAA 模式
- [ ] 使用 `StepVerifier` 测试响应式代码
- [ ] Mock 了所有外部依赖
- [ ] 测试覆盖正常路径和异常路径
- [ ] 没有使用 `Thread.sleep()` (除非必要)
- [ ] 没有依赖测试执行顺序
- [ ] 测试数据使用 `TestDataFactory` 创建
- [ ] 没有硬编码敏感信息

## 更多信息

- 详细示例: 见 [examples.md](examples.md)
- 技术栈和配置: 见 [reference.md](reference.md)
